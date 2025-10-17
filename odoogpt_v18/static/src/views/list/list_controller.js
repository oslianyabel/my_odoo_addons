/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
const { Component } = owl;

patch(ListController.prototype, {
    onSelectDesoftBot(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const rpc = this.env.services.rpc;

        rpc('/web/dataset/call_kw', {
            model: 'res.partner',
            method: 'open_desoft_bot',
            args: [[], this.model.rootParams],
            kwargs: {},
        }).then(async (res) => {
            await this._openChat({ userId: res });  // ✅ Usar _openChat
        });
        console.log("Inside onSelectDesoftBot event");
    },

    async _openChat(params) {
        const messagingService = this.env.services.messaging;
        if (!messagingService) {
            console.error("Messaging service not available!");
            return;
        }
        const messaging = await messagingService.get();
        messaging.openChat(params);  // ✅ Usar openChat, no openChannel
    }
});
