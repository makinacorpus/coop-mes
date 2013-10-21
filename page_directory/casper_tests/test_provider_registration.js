casper.test.comment('Provider registration');

var helper = require('./djangocasper.js');

helper.scenario('/annuaire/p/ajouter/',
    function() {
        this.sendKeys('#id_last_name', 'Casper1');
        this.sendKeys('#id_email', 'casper@casper.js');
        this.sendKeys('#id_username', 'casper1');
        this.sendKeys('#id_password1', 'casper');
        this.sendKeys('#id_password2', 'casper');
        this.sendKeys('#id_title', 'Casper1');
        this.click('#id_is_provider');
        this.click('#id_charte_2');
    }
    , function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForSelector('#id_birth');
    }
    , function() {
        this.click('#id_birth');
    }
    , function() {
        this.waitForSelector('td.day.active');
    }
    , function() {
        this.click('td.day.active');
    }
    , function() {
        this.mouseEvent('mousedown', '#s2id_id_legal_status b');
    }
    , function() {
        this.waitForSelector('.select2-results');
    }
    , function() {
        this.sendKeys('.select2-input.select2-focused', 'asso');
    }
    , function() {
        this.mouseEvent('mouseup', '.select2-result-label');
    }
    , function() {
        this.sendKeys('#id_siret', '12345678901234');
    }
    , function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForSelector('#id_brief_description');
    }
    , function() {
        this.sendKeys('#id_brief_description', 'Casper blabla blabla.');
    }
    , function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForSelector('#div_id_tags');
    }
    , function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForSelector('#id_workforce');
    }
    , function() {
        this.sendKeys('#id_workforce', '10');
        this.sendKeys('#id_integration_workforce', '5');
        this.sendKeys('#id_annual_integration_number', '20');
    }
    , function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForSelector('#id_testimony');
    }
    , function() {
        this.open(this.cli.options['url-base'] + '/annuaire/p/offre/ajouter/');
    }
    , function() {
        this.click('#id_targets_2');
    }
    , function() {
        this.sendKeys('#s2id_id_activity .select2-input', 'aqua');
    }
    , function() {
        this.mouseEvent('mouseup', '.select2-result-label');
    }
    , function() {
        this.sendKeys('#s2id_id_area .select2-input', 'barl');
    }
    , function() {
        this.mouseEvent('mouseup', '.select2-result-label');
    }
    , function() {
        this.click('form.form-horizontal button.btn-default');
    }
    , function() {
        this.waitForText('MES OFFRES');
    }
    , function() {
        this.open(this.cli.options['url-base'] + '/annuaire/p/modifier/');
    }
    , function() {
        this.click('form.form-horizontal button.btn--form');
    }
    , function() {
        this.waitForText('MON COMPTE');
    }
    , function() {
        this.open(this.cli.options['url-base'] + '/annuaire/p/modifier/');
    }
    , function() {
        this.test.assertTextExists('Votre fiche est en cours de validation par les administrateurs du site');
    }
);

helper.run();
