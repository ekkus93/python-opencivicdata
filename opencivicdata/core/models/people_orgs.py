from __future__ import unicode_literals
import datetime
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.encoding import python_2_unicode_compatible
from .base import OCDBase, LinkBase, OCDIDField, RelatedBase, IdentifierBase
from .division import Division
from .jurisdiction import Jurisdiction
from ... import common

# abstract models


@python_2_unicode_compatible
class ContactDetailBase(RelatedBase):
    """
    A base class for ContactDetail models.
    """
    type = models.CharField(
        max_length=50,
        choices=common.CONTACT_TYPE_CHOICES,
        help_text="The type of Contact being defined.",
    )
    value = models.CharField(
        max_length=300,
        help_text="The content of the Contact information like a phone number or email address."
    )
    note = models.CharField(
        max_length=300,
        blank=True,
        help_text="A short, optional note about the Contact value."
    )
    label = models.CharField(
        max_length=300,
        blank=True,
        help_text="A title for the content of the Contact."
    )

    class Meta:
        abstract = True

    def __str__(self):
        return '{}: {}'.format(self.get_type_display(), self.value)


@python_2_unicode_compatible
class OtherNameBase(RelatedBase):
    """
    A base class for OtherName models.
    """
    name = models.CharField(
        max_length=500,
        db_index=True,
        help_text="An alternative name.",
    )
    note = models.CharField(
        max_length=500, blank=True,
        help_text="A short, optional note about alternative name.",
    )
    start_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="An optional start date for usage of the alternative name "
                  "in YYYY[-MM[-DD]] string format.",
    )
    end_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="An optional end date for usage of the alternative name in "
                  "YYYY[-MM[-DD]] string format.",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return '{} ({})'.format(self.name, self.note)


# the actual models

@python_2_unicode_compatible
class Organization(OCDBase):
    """
    A group of people, typically in a legislative or rule-making context.
    """
    id = OCDIDField(ocd_type='organization')
    name = models.CharField(max_length=300, help_text="The name of the Organization.")
    image = models.URLField(
        blank=True,
        max_length=2000,
        help_text="A URL leading to an image that identifies the Organization visually."
    )
    parent = models.ForeignKey(
        'self',
        related_name='children',
        null=True,
        help_text="A link to another Organization that serves as this Organization's parent."
    )
    jurisdiction = models.ForeignKey(
        Jurisdiction,
        related_name='organizations',
        null=True,
        help_text="A link to the Jurisdiction that contains this Organization.",
    )
    classification = models.CharField(
        max_length=100,
        blank=True,
        choices=common.ORGANIZATION_CLASSIFICATION_CHOICES,
        help_text="The type of Organization being defined."
    )
    founding_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="The founding date of the Organization in YYYY[-MM[-DD]] string format."
    )
    dissolution_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="The dissolution date of the Organization in YYYY[-MM[-DD]] string format."
    )

    def __str__(self):
        return self.name

    # Access all "ancestor" organizations
    def get_parents(self):
        org = self
        while True:
            org = org.parent
            # Django accesses parents lazily, so have to check if one actually exists
            if org:
                yield org
            else:
                break

    def get_current_members(self):
        """ return all Person objects w/ current memberships to org """
        today = datetime.date.today().isoformat()

        return Person.objects.filter(Q(memberships__start_date='') |
                                     Q(memberships__start_date__lte=today),
                                     Q(memberships__end_date='') |
                                     Q(memberships__end_date__gte=today),
                                     memberships__organization_id=self.id
                                     )

    class Meta:
        db_table = 'opencivicdata_organization'
        index_together = [
            ['jurisdiction', 'classification', 'name'],
            ['classification', 'name'],
        ]


@python_2_unicode_compatible
class OrganizationIdentifier(IdentifierBase):
    """
    Upstream identifiers of an Organization.
    """
    organization = models.ForeignKey(
        Organization,
        related_name='identifiers',
        help_text="Reference to the Organization identified by this alternative identifier.",
    )

    def __str__(self):
        tmpl = '%s identifies %s'
        return tmpl % (self.identifier, self.organization)

    class Meta:
        db_table = 'opencivicdata_organizationidentifier'


class OrganizationName(OtherNameBase):
    """
    Alternate or former name for an Organization.
    """
    organization = models.ForeignKey(
        Organization,
        related_name='other_names',
        help_text="A link to the Organization with this alternative name.",
    )

    class Meta:
        db_table = 'opencivicdata_organizationname'


class OrganizationContactDetail(ContactDetailBase):
    """
    Contact information for an Organization.
    """
    organization = models.ForeignKey(
        Organization,
        related_name='contact_details',
        help_text="A link to the Organization connected to this contact."
    )

    class Meta:
        db_table = 'opencivicdata_organizationcontactdetail'


class OrganizationLink(LinkBase):
    """
    URL for a document about an Organization.
    """
    organization = models.ForeignKey(
        Organization,
        related_name='links',
        help_text="A reference to the Organization connected to this link."
    )

    class Meta:
        db_table = 'opencivicdata_organizationlink'


class OrganizationSource(LinkBase):
    """
    Source used in assembling an Organization.
    """
    organization = models.ForeignKey(
        Organization,
        related_name='sources',
        help_text="A link to the Organization connected to this source."
    )

    class Meta:
        db_table = 'opencivicdata_organizationsource'


@python_2_unicode_compatible
class Post(OCDBase):
    """
    A position in an organization that exists independently of the person holding it.
    """
    id = OCDIDField(ocd_type='post')
    label = models.CharField(max_length=300, help_text="A label describing the Post.")
    role = models.CharField(
        max_length=300,
        blank=True,
        help_text="The function that the holder of the post fulfills."
    )
    organization = models.ForeignKey(
        Organization,
        related_name='posts',
        help_text="The Organization in which the post is held."
    )
    division = models.ForeignKey(
        Division,
        related_name='posts',
        null=True,
        blank=True,
        default=None,
        help_text="The Division where the post exists."
    )
    start_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="An optional start date for the Post in YYYY[-MM[-DD]] string format."
    )
    end_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="An optional end date for the Post in YYYY[-MM[-DD]] string format."
    )
    maximum_memberships = models.PositiveIntegerField(
        default=1,
        help_text="The maximum number of people who can hold this Post."
    )

    class Meta:
        db_table = 'opencivicdata_post'
        index_together = [
            ['organization', 'label']
        ]

    def __str__(self):
        return '{} - {} - {}'.format(self.role, self.label, self.organization)


class PostContactDetail(ContactDetailBase):
    """
    Contact information for whoever currently occupies a Post.
    """
    post = models.ForeignKey(
        Post,
        related_name='contact_details',
        help_text="A link to the Post connected to this contact."
    )

    class Meta:
        db_table = 'opencivicdata_postcontactdetail'


class PostLink(LinkBase):
    """
    URL for a document about a Post.
    """
    post = models.ForeignKey(
        Post,
        related_name='links',
        help_text="A reference to the Post connected to this link."
    )

    class Meta:
        db_table = 'opencivicdata_postlink'


class PersonQuerySet(QuerySet):
    def member_of(self, organization_name, current_only=True):
        filter_params = []

        if current_only:
            today = datetime.date.today().isoformat()

            filter_params = [Q(memberships__start_date='') |
                             Q(memberships__start_date__lte=today),
                             Q(memberships__end_date='') |
                             Q(memberships__end_date__gte=today),
                             ]
        if organization_name.startswith('ocd-organization/'):
            qs = self.filter(*filter_params,
                             memberships__organization_id=organization_name)
        else:
            qs = self.filter(*filter_params,
                             memberships__organization__name=organization_name)
        return qs


@python_2_unicode_compatible
class Person(OCDBase):
    """
    An individual that has served in a political office.
    """
    objects = PersonQuerySet.as_manager()

    id = OCDIDField(ocd_type='person')
    name = models.CharField(
        max_length=300,
        db_index=True,
        help_text="A Person's preferred full name."
    )
    sort_name = models.CharField(
        max_length=100,
        default='',
        blank=True,
        help_text="A version of a Person's full name rearranged for alphabetical sorting."
    )
    family_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="A Person's family name."
    )
    given_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="A Person's given name."
    )
    image = models.URLField(
        blank=True,
        max_length=2000,
        help_text="A URL leading to an image that identifies the Person visually."
    )
    gender = models.CharField(
        max_length=100,
        blank=True,
        help_text="A Person's gender"
    )
    summary = models.CharField(
        max_length=500,
        blank=True,
        help_text="A short, one-line account of a Person's life."
    )
    national_identity = models.CharField(
        max_length=300,
        blank=True,
        help_text="The nation a Person is identified with."
    )
    biography = models.TextField(
        blank=True,
        help_text="An extended account of a Person's life."
    )
    birth_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="The date of a Person's birth in YYYY[-MM[-DD]] string format."
    )
    death_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="The date of a Person's death in YYYY[-MM[-DD]] string format."
    )

    def __str__(self):
        return self.name

    def add_other_name(self, name, note=""):
        PersonName.objects.create(name=name, note=note, person_id=self.id)

    class Meta:
        db_table = 'opencivicdata_person'
        verbose_name_plural = "people"


class PersonIdentifier(IdentifierBase):
    """
    Upstream identifier for a Person.
    """
    person = models.ForeignKey(
        Person,
        related_name='identifiers',
        help_text="A link to the Person connected to this alternative identifier."
    )

    class Meta:
        db_table = 'opencivicdata_personidentifier'


class PersonName(OtherNameBase):
    """
    Alternate or former name of a Person.
    """
    person = models.ForeignKey(
        Person,
        related_name='other_names',
        help_text="A link to the Person connected to this alternative name."
    )

    class Meta:
        db_table = 'opencivicdata_personname'


class PersonContactDetail(ContactDetailBase):
    """
    Contact information for a Person.
    """
    person = models.ForeignKey(
        Person,
        related_name='contact_details',
        help_text="A link to the Person connected to this contact."
    )

    class Meta:
        db_table = 'opencivicdata_personcontactdetail'


class PersonLink(LinkBase):
    """
    URL for a document about a Person.
    """
    person = models.ForeignKey(
        Person,
        related_name='links',
        help_text="A reference to the Person connected to this link."
    )

    class Meta:
        db_table = 'opencivicdata_personlink'


class PersonSource(LinkBase):
    """
    Source used in assembling a Person.
    """
    person = models.ForeignKey(
        Person,
        related_name='sources',
        help_text="A link to the Person connected to this source."
    )

    class Meta:
        db_table = 'opencivicdata_personsource'


@python_2_unicode_compatible
class Membership(OCDBase):
    """
    A relationship between a Person and an Organization, possibly including a Post.
    """
    id = OCDIDField(ocd_type='membership')
    organization = models.ForeignKey(
        Organization,
        related_name='memberships',
        help_text="A link to the Organization in which the Person is a member."
    )
    person = models.ForeignKey(
        Person,
        related_name='memberships',
        null=True,
        help_text="A link to the Person that is a member of the Organization."
    )
    person_name = models.CharField(
        max_length=300,
        blank=True,
        default='',
        help_text="The name of the Person that is a member of the Organization."
    )
    post = models.ForeignKey(
        Post,
        related_name='memberships',
        null=True,
        help_text="	The Post held by the member in the Organization."
    )
    on_behalf_of = models.ForeignKey(
        Organization,
        related_name='memberships_on_behalf_of',
        null=True,
        help_text="The Organization on whose behalf the Person is a member of the Organization."
    )
    label = models.CharField(
        max_length=300,
        blank=True,
        help_text="A label describing the membership."
    )
    role = models.CharField(
        max_length=300,
        blank=True,
        help_text="The role that the member fulfills in the Organization."
    )
    start_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="The date on which the relationship began in YYYY[-MM[-DD]] string format."
    )
    end_date = models.CharField(
        max_length=10,
        blank=True,
        help_text="The date on which the relationship ended in YYYY[-MM[-DD]] string format."
    )

    class Meta:
        db_table = 'opencivicdata_membership'
        index_together = [
            ['organization', 'person', 'label', 'post']
        ]

    def __str__(self):
        return '{} in {} ({})'.format(self.person, self.organization, self.role)


class MembershipContactDetail(ContactDetailBase):
    """
    Contact information for Person at an Organization.
    """
    membership = models.ForeignKey(
        Membership,
        related_name='contact_details',
        help_text="A link to the Membership connected to this contact."
    )

    class Meta:
        db_table = 'opencivicdata_membershipcontactdetail'


class MembershipLink(LinkBase):
    """
    URL for a document about a Person's relationship to an Organization.
    """
    membership = models.ForeignKey(
        Membership,
        related_name='links',
        help_text="A reference to the Membership connected to this link."
    )

    class Meta:
        db_table = 'opencivicdata_membershiplink'
