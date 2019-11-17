odoo.define('perso_account.AccountStructure', function (require) {
    "use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var qweb = core.qweb;


//TODO List of account
//TODO list of period
//TODO default expand

var ClientAction = AbstractAction.extend(ControlPanelMixin, {
    template: 'account.structure',
    events: {
        'click tbody tr td': '_onExpendClicked',
        'click .budget': '_onClickBudget',
    },
    willStart: function() {
        var self = this;
        this.period_id = 'current';
        this.hide = false;
        var def = this.loadData();
        return $.when(this._super(), def);
    },
    start: function () {
        this._renderButtons();
        this._renderSearchButtons();
        this._updateControlPanel();
        this.close_all();
    },
    do_show: function () {
        this._super.apply(this, arguments);
        this._updateControlPanel();
    },
    loadData: function() {
        var self = this;
        return this._rpc({
            'model': 'perso.account',
            'method': 'get_structure',
            'args': [],
            'kwargs': {
                'hide': self.hide,
                'context': {'period_id': self.period_id}
            }, 
        }).then(function(result) {
                self.structure = result[0];
                self.budget_per_account = result[1];
        });
    },
    reload: function() {
        var self = this;
        this.loadData().then(function() {
            self.renderElement();
            self.close_all();
        })
    },
    close_all: function() {
        this._hide_children(this.$('.root'));
    },
    expand_all: function() {
        var fa = this.$el.find('.fa');
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
            var html_budget = "<input type='text' class='budget-"+ account_id  + " input-budget'  value='"+ this.budget_per_account[this.account_budget_id] + "'/>";
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
        this.$searchview_buttons = $(qweb.render('account.structure.search_button'));
        this.$searchview_buttons.find('.period').click(function(event) {
            self.$searchview_buttons.find('.period').toggleClass('selected', false);
            var period = $(this).data('filter');
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
            $(this).toggleClass('selected', true);
            self.reload();
        });
    },
    _updateControlPanel: function () {
        this.update_control_panel({
            cp_content: {
                $buttons: this.$buttons,
                $searchview_buttons: this.$searchview_buttons
            },
        })
    },
});

core.action_registry.add('account_structure', ClientAction);

return {
    ClientAction: ClientAction,
};

});