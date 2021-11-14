odoo.define('perso_account.AccountStructure', function (require) {
"use strict";

//var ControlPanelMixin = require('web.ControlPanelMixin');
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var qweb = core.qweb;


//TODO List of account
//TODO list of period
//TODO default expand

var ClientAction = AbstractAction.extend({
    hasControlPanel: true,
    //loadControlPanel: true,
    contentTemplate: 'account.structure',
    events: {
        'click tbody tr td': '_onExpendClicked',
        'click .budget': '_onClickBudget',
    },
    willStart: function() {
        var self = this;
        this.period_id = 'current';
        this.hide = false;
        var def = this.loadData();
        var def2 = this.loadFilterData();
        return $.when(this._super(), def, def2);
    },
    start: async function () {
        this._renderButtons();
        this._renderSearchButtons();
        this.controlPanelProps.cp_content = {
            $buttons: this.$buttons,
            $searchview_buttons: this.$searchview_buttons
        }
        await this._super(...arguments);
        this.close_all();
    },
    loadData: function() {
        var self = this;
        return this._rpc({
            'model': 'perso.account',
            'method': 'get_structure',
            'args': [],
            'kwargs': {
                'hide': self.hide,
                'context': {'period_id': self.period_id, 'bank_ids': self.bank_ids}
            }, 
        }).then(function(result) {
                self.structure = result[0];
                self.budget_per_account = result[1];
        });
    },
    loadFilterData: function() {
        var self = this;
        var def1 = this._rpc({
            'model': 'perso.bank.account',
            'method': 'name_search',
            'args': [''],
        }).then(function(result) {
            self.bank_list = result;
            self.bank_ids = []
        });
        var def2 = this._rpc({
            'model': 'perso.account.period',
            'method': 'name_search',
            'args': [''],
        }).then(function(result) {
            self.period_list = result;
        });
        return $.when(def1, def2);
    },
    reload: function() {
        var self = this;
        this.loadData().then(function() {
            const content = core.qweb.render(self.contentTemplate, { widget: self });
            self.$('.o_content').empty();
            self.$('.o_content').append(content);
            self.close_all();
        })
    },
    close_all: function() {
        this._hide_children(this.$('.root'));
    },
    expand_all: function() {
        var fa = this.$el.find('.fa-caret-right, .fa-caret-down');
        fa.removeClass('fa-caret-right');
        fa.addClass('fa-caret-down');
        this.$el.find('tr').show();
    },
    _onExpendClicked: function(event) {
        var id = event.currentTarget.id;
        var fa = $(event.currentTarget).find('.fa');
        fa.toggleClass('fa-caret-down');
        fa.toggleClass('fa-caret-right');
        if (!!id) {
            var children = this.$el.find('.' + id);
            if(children.is(':hidden') === false) {
                this._hide_children(children);
            }
            children.toggle();
        }
    },
    _onClickBudget: function(event) {
        self = this
        var account_id = parseInt(event.currentTarget.id);
        if (!! this.account_budget_id && this.account_budget_id != account_id) {
            var previous_budget = this.$el.find("#" + this.account_budget_id);
            previous_budget.html("<span>" + this.budget_per_account[this.account_budget_id] + "</span>")
        }
        if(this.account_budget_id != account_id) {
            var span = $(event.currentTarget).children();
            this.account_budget_id = account_id;
            $('#' + this.account_budget_id).off('click');
            var html_budget = "<input type='text' style='display:inline' class='budget-"+ account_id  + " input-budget'  value='"+ this.budget_per_account[this.account_budget_id] + "'/>";
            html_budget += "<button type='button' id='button-budget-"+ account_id +"' class='btn btn-link btn-budget'>validate</button>";
            span.html(html_budget);
            this.$el.find('.btn-budget').click(function(event) {
                var budget_val = parseInt(self.$el.find('.input-budget').val())
                if (!!budget_val) {
                    self._rpc({
                        'model': 'perso.account',
                        'method': 'write',
                        'args': [[self.account_budget_id], {'budget': budget_val}],
                        'kwargs': {
                            'context': {'period_id': self.period_id}
                        },
                    }).then(function(result) {
                        self.reload();
                    });
                }
                //TODO else show bad input popup
            });
        }
    },
    _get_bank_ids: function(bank_list) {
        return bank_list.reduce((prev, cur) => prev.concat([cur[0]]), [])
    },
    _hide_children: function(node_list) {
        var nodes = node_list.find('td');
        var fa = nodes.find('.fa');
        fa.removeClass('fa-caret-down');
        fa.addClass('fa-caret-right');
        for(var i=0; i < nodes.length; i++) {
            if(nodes[i].id != "") {
                var children = this.$el.find('.' + nodes[i].id);
                this._hide_children(children);
                children.hide();

            }
        }
    },
    _renderButtons: function () {
        var self = this;
        this.$buttons = $(qweb.render('account.structure.button'));
        this.$buttons.find('.close-all').click(function(event) {
            self.close_all();
        });
        this.$buttons.find('.expand-all').click(function(event) {
            self.expand_all();
        });

    },
    _renderSearchButtons: function () {
        var self = this;
        this.$searchview_buttons = $(qweb.render('account.structure.search_button', {
            bank_list: this.bank_list,
            period_list: this.period_list,
        }));
        this.$searchview_buttons.find('.period').click(function(event) {
            self.$searchview_buttons.find('.period').toggleClass('selected', false);
            var period = $(this).data('filter');
            self.$searchview_buttons.find('.period-name').html($(this).attr('title'))
            if (self.period_id != period) {
                $(this).toggleClass('selected', true);
                self.period_id = period;
                self.reload();
            }
            else {
                self.period_id = false;
                self.reload();
            }
        });
        this.$searchview_buttons.find('.filter').click(function(event) {
            self.$searchview_buttons.find('.filter').toggleClass('selected', false);
            self.hide = $(this).data('hide');
            self.$searchview_buttons.find('.filter-name').html($(this).attr('title'))
            $(this).toggleClass('selected', true);
            self.reload();
        });
        this.$searchview_buttons.find('.bank').click(function(event) {
            //self.$searchview_buttons.find('.bank').toggleClass('selected', false);
            var bank = $(this).data('bank');
            if (bank == 'none') {
                self.$searchview_buttons.find('.bank-id').toggleClass('selected', false);
                self.bank_ids = []
            }
            else if (bank == 'all') {
                self.$searchview_buttons.find('.bank-id').toggleClass('selected', true);
                self.bank_ids = self._get_bank_ids(self.bank_list)
            }
            else {
                $(this).toggleClass('selected');
                if ($(this).hasClass('selected')) {
                    self.bank_ids = self.bank_ids.concat([bank])
                }
                else {
                    self.bank_ids = self.bank_ids.filter(b => b != bank)
                }
            }
            self.reload();
        });
    },
    update_cp: function () {
        this._renderButtons();
        this._renderSearchButtons();
        this.controlPanelProps.cp_content = {
            $buttons: this.$buttons,
            $searchview_buttons: this.$searchview_buttons
        }
        return this.updateControlPanel()
    },
});

core.action_registry.add('account_structure', ClientAction);

return {
    ClientAction: ClientAction,
};

});