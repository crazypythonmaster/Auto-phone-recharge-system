/**
 * GETparams
 *
 * Created by eugene-s
 *
 * TODO: documentation...
 *
 * 2015
 */

GETparams = new (function() {
    var sPageURL = window.location.search.substring(1),
        sURLVariables = sPageURL.split('&'),
        data = {
            sParams: [],
            params: {}
        };

    for (var i = 0; i < sURLVariables.length; i++) {
        var sParameterName = sURLVariables[i].split('=');
        data.params[sParameterName[0]] = {
            val: sParameterName[1],
            used: false
        };
        data.sParams.push(sParameterName[0]);
    }

    GETparam = function(param, callback) {
        if (typeof callback == 'function') {
            return callback.call({
                check: function () {
                    return GETparams.check(param);
                },
                val: function () {
                    return GETparams.val(param);
                },
                used: function (option) {
                    return GETparams.used(param, option);
                }
            });
        } else {
            if (GETparams.check(param)) {
                return GETparams.val(param);
            }
        }
    };

    this.check = function (param) {
        return data.params[param] ? true : false;
    };
    this.val = function (param) {
        return data.params[param].val;
    };
    this.used = function (param, option) {
        if (typeof option == 'boolean') {
            data.params[param].used = option;
        }
    };
    this.list = function () {
        return data.sParams;
    };
})();