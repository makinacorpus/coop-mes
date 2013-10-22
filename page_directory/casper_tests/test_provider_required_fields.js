casper.test.comment('Provider required fields');

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
        this.capture('provider_required_step0.png');
        this.test.assertExists('#div_id_last_name.has-error');
        this.test.assertExists('#div_id_email.has-error');
        this.test.assertExists('#div_id_username.has-error');
        this.test.assertExists('#div_id_password1.has-error');
        this.test.assertExists('#div_id_password2.has-error');
        this.test.assertExists('#div_id_title.has-error');
        this.test.assertExists('#div_id_charte.has-error');
        this.test.assertTextExists('Veuillez cocher une des cases Fournisseur ou Acheteur');
        this.fill('form.form-horizontal', {
            last_name: 'Casper2'
            , email: 'casper@casper.js'
            , username: 'casper2'
            , password1: 'casper'
            , password2: 'casper'
            , title: 'Casper2'
            , charte: '1'
            , is_provider: true
            , is_customer: false
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
        this.capture('provider_required_step1.png');
        this.test.assertExists('#div_id_birth.has-error');
        this.test.assertExists('#div_id_legal_status.has-error');
        this.test.assertExists('#div_id_siret.has-error');
        this.fill('form.form-horizontal', {
            birth: '2013-10-21'
            , legal_status: '1'
            , siret: '12345678901234'
        });
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForSelector('#div_id_brief_description');
    }
    , function() {
        this.capture('provider_required_step2.png');
        this.test.assertExists('#div_id_brief_description.has-error');
        this.fill('form.form-horizontal', {
            brief_description: 'Blabla.'
        });
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForSelector('#div_id_workforce');
    }
    , function() {
        this.capture('provider_required_step3.png');
        this.test.assertExists('#div_id_workforce.has-error');
        this.fill('form.form-horizontal', {
            workforce: '1,5'
        });
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForText('Veuillez ajouter au moins une offre');
    }
    , function() {
        this.capture('provider_required_step4.png');
        this.test.assertTextExists('Veuillez ajouter au moins une offre');
    }
);

helper.run();
