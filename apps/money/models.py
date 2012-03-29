#__author__ = 'root'
from datetime import datetime
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.contenttypes.generic import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.db import models
from nnmware.apps.address.models import Country
from nnmware.core.managers import TransactionManager

class Currency(models.Model):
    code = models.CharField(max_length=3, verbose_name=_('Currency code'))
    country = models.ForeignKey(Country, verbose_name=_('Country'), on_delete=models.SET_NULL, blank=True, null=True)
    name = models.CharField(verbose_name=_("Name"), max_length=100)
    name_en = models.CharField(verbose_name=_("Name(English"), max_length=100, blank=True)

    class Meta:
        unique_together = ('code',)
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")

    def __unicode__(self):
        return u"%s :: %s" % (self.code, self.name)

class ExchangeRate(models.Model):
    currency = models.ForeignKey(Currency, verbose_name=_('Currency'), on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(verbose_name=_('On date'))
    rate = models.DecimalField(verbose_name=_('Rate'), default=0.0, max_digits=10, decimal_places=3)

    class Meta:
        unique_together = ('currency','date','rate')
        verbose_name = _("Exchange Rate")
        verbose_name_plural = _("Exchange Rates")


class MoneyBase(models.Model):
    amount = models.DecimalField(verbose_name=_('Amount'), default=0.0, max_digits=20, decimal_places=3)
    currency = models.ForeignKey(Currency, verbose_name=_('Currency'), on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        abstract = True

TRANSACTION_UNKNOWN = 0
TRANSACTION_ACCEPTED = 1
TRANSACTION_COMPLETED = 2
TRANSACTION_CANCELED = 3

TRANSACTION_STATUS = (
    (TRANSACTION_UNKNOWN, _("Unknown")),
    (TRANSACTION_ACCEPTED, _("Accepted")),
    (TRANSACTION_COMPLETED, _("Completed")),
    (TRANSACTION_CANCELED, _("Cancelled")),
    )


class Transaction(MoneyBase):
    """
    Transaction(no more words)
    """
    user = models.ForeignKey(User, verbose_name=_("User"))

    content_type = models.ForeignKey(ContentType, verbose_name=_("Content Type"), null=True, blank=True, on_delete=models.SET_NULL)
    object_id = models.CharField(max_length=255, verbose_name=_("ID of object"), null=True, blank=True)
    actor = GenericForeignKey()
    date = models.DateTimeField(verbose_name=_("Date"), default=datetime.now())
    status = models.IntegerField(_("Transaction status"), choices=TRANSACTION_STATUS, default=TRANSACTION_UNKNOWN)

    objects = TransactionManager()

    class Meta:
        unique_together = ('user', 'content_type', 'object_id', 'date', 'amount','currency')
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __unicode__(self):
        return u'%s -> %s' % (self.user, self.actor)

    def __unicode__(self):
        return _("User: %(user)s :: Date: %(date)s :: Object: %(actor)s :: Amount: %(amount)s %(currency)s") %\
                   { 'user': self.user.username,
                     'date': self.date,
                     'actor': self.actor,
                     'amount': self.amount,
                     'currency': self.currency.code}