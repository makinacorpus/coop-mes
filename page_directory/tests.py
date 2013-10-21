from coop_local.models import Organization, Offer
from casper.tests import CasperTestCase
import os.path

class SignInTestCase(CasperTestCase):

    #def _fixture_setup(self):
        #pass

    fixtures = [
        'activitynomenclatureavise.json',
        'activitynomenclature.json',
        'agreementiae.json',
        'area_types.json',
        'categoryiae.json',
        'clienttarget.json',
        'contact_mediums.json',
        'test_django_site.json',
        'exchange_methods.json',
        'group.json',
        'guaranty.json',
        'legalstatus.json',
        'linking_properties.json',
        'location_categories.json',
        'organizationcategory.json',
        'relation_types.json',
        'roles.json',
        'transversetheme.json',
        'user.json',
    ]

    def test_registration(self):
        self.assertTrue(self.casper(
            os.path.join(
                os.path.dirname(__file__),
                'casper_tests',
                'test_provider_registration.js'
            )
        ))
        self.assertTrue(Organization.objects.filter(title='Casper1').exists())
        provider = Organization.objects.get(title='Casper1')
        self.assertEqual(provider.status, 'P')
        self.assertTrue(provider.offer_set.exists())
        self.assertTrue(self.casper(
            os.path.join(
                os.path.dirname(__file__),
                'casper_tests',
                'test_provider_required_fields.js'
            )
        ))
        self.assertTrue(self.casper(
            os.path.join(
                os.path.dirname(__file__),
                'casper_tests',
                'test_customer_registration.js'
            )
        ))
        self.assertTrue(Organization.objects.filter(title='Casper3').exists())
        provider = Organization.objects.get(title='Casper3')
        self.assertEqual(provider.status, 'P')
        self.assertTrue(provider.offer_set.exists())
        self.assertTrue(self.casper(
            os.path.join(
                os.path.dirname(__file__),
                'casper_tests',
                'test_customer_required_fields.js'
            )
        ))
