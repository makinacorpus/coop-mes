casper.test.comment('Customer required fields');

var helper = require('./djangocasper.js');
var baseurl = casper.cli.options['url-base'];

helper.scenario('/annuaire/p/ajouter/',
    function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForSelector('#div_id_last_name');
    }
    , function() {
        this.capture('customer_required_step0.png');
        this.test.assertExists('#div_id_last_name.has-error');
        this.test.assertExists('#div_id_email.has-error');
        this.test.assertExists('#div_id_username.has-error');
        this.test.assertExists('#div_id_password1.has-error');
        this.test.assertExists('#div_id_password2.has-error');
        this.test.assertExists('#div_id_title.has-error');
        this.test.assertExists('#div_id_charte.has-error');
        this.test.assertTextExists('Veuillez cocher une des cases Fournisseur ou Acheteur');
        this.fill('form.form-horizontal', {
            last_name: 'Casper4'
            , email: 'casper@casper.js'
            , username: 'casper4'
            , password1: 'casper'
            , password2: 'casper'
            , title: 'Casper4'
            , charte: '1'
            , is_provider: false
            , is_customer: true
        });
    }
    , function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForSelector('#div_id_birth');
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForSelector('#div_id_birth');
    }
    , function() {
        this.capture('customer_required_step1.png');
        this.test.assertExists('#div_id_logo.has-error');
        this.test.assertExists('#div_id_birth.has-error');
        this.test.assertExists('#div_id_legal_status.has-error');
        this.test.assertExists('#div_id_web.has-error');
        this.test.assertExists('#div_id_customer_type.has-error');
        this.fill('form.form-horizontal', {
              logo: 'logo.jpeg'
            , birth: '2013-10-21'
            , legal_status: '1'
            , web: 'www.casper.js'
            , customer_type: '1'
        });
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForSelector('#div_id_brief_description');
    }
    , function() {
        this.capture('customer_required_step2.png');
        this.test.assertExists('#div_id_brief_description.has-error');
        this.test.assertExists('#div_id_description.has-error');
        this.fill('form.form-horizontal', {
              brief_description: 'Casper blabla.'
        });
    }
    , function() {
        this.waitForSelector('#id_description_ifr');
    }
    , function() {
        this.evaluate(function() {
            tinyMCE.activeEditor.setContent('Casper blabla blabla.');
        });
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForSelector('#div_id_tags');
    }
    , function() {
        this.capture('customer_required_step3.png');
        this.test.assertExists('#div_id_tags.has-error');
    }
    , function() {
        this.waitForSelector('#id_tags__tagautosuggest');
    }
    , function() {
        this.sendKeys('#id_tags__tagautosuggest', 'ESS,');
    }
    , function() {
        this.waitForSelector('.as-selection-item');
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForText('MON COMPTE');
    }
);

helper.run();
