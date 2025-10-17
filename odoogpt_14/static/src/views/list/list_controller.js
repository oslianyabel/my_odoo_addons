odoo.define('odoogpt.ListController', function (require) {
"use strict";

var ListController = require('web.ListController');
var core = require('web.core');

ListController.include({
    renderButtons: function ($node) {
        this._super.apply(this, arguments);
        if (this.$buttons) {
            this.$buttons.on('click', '.o_list_button_desoft_bot', this._onSelectDesoftBot.bind(this));
        }
    },

    _onSelectDesoftBot: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var self = this;

        this._rpc({
            model: 'res.partner',
            method: 'open_odoogpt',
            args: [[], this.initialState.context],
        }).then(function (userId) {
            self.do_action('mail.action_discuss', {
                active_id: 'mail.channel_' + userId,
                additional_context: {
                    default_channel_id: userId,
                },
            });
        });
    },
});

return ListController;

});
