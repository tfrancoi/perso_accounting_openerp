odoo.define('perso_account.AccountStructure', function (require) {
    "use strict";

var ControlPanelMixin = require('web.ControlPanelMixin');
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var qweb = core.qweb;


var ClientAction = AbstractAction.extend(ControlPanelMixin, {
    template: 'account.structure',
    events: {
        'click tbody tr td': '_onExpendClicked',
    },
    willStart: function() {
        var self = this;
        var def = this._rpc({
            'model': 'perso.account',
            'method': 'get_structure',
            'args': []}).then(function(result) {
                self.structure = result;
        });
        return $.when(this._super(), def);
    },
    start: function () {
        this._hide_children(this.$('.root'));
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

    _hide_children: function(node_list) {
        var nodes = node_list.find('td');
        var fa = nodes.find('.fa');
        fa.removeClass('fa-caret-down');
        fa.addClass('fa-caret-right')
        for(var i=0; i < nodes.length; i++) {
            if(nodes[i].id != "") {
                var children = this.$el.find('.' + nodes[i].id);
                this._hide_children(children);
                children.hide();

            }
        }
    },
});

core.action_registry.add('account_structure', ClientAction);

return {
    ClientAction: ClientAction,
};

});