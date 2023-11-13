odoo.define('od_purchase_order_workflow.NotificationManager', function (require) {
    "use strict";

    var AbstractService = require('web.AbstractService');
    var core = require("web.core");
    var SHNotificationManager = AbstractService.extend({
        dependencies: ['bus_service'],

        /**
         * @override
         */
        start: function () {
            this._super.apply(this, arguments);
            this.call('bus_service', 'onNotification', this, this._onNotification);
        },

        _onNotification: function (notifications) {
            for (const { payload, type } of notifications) {
                if (type === "sh_notification_info") {
                    this.displayNotification({ title: payload.title, message: payload.message, type: 'info', sticky: true });
                }
                if (type === "sh_notification_alert") {
                    this.displayNotification({ title: payload.title, message: payload.message, type: 'danger', sticky: true });
                }
            }
        }

    });

    core.serviceRegistry.add('sh_notification_service', SHNotificationManager);

    return SHNotificationManager;

});