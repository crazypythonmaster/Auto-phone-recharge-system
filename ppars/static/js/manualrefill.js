function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++)
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam)
        {
            return sParameterName[1];
        }
    }
}

$(document).ready(function(){
    function getSellingPrice(plan_id, customer_id, count){
        // Somewhere on the page should be element with id "selling_price", price will be displayed there
        $.ajax({
            url: '/ajax_get_plan_selling_price',
            data: {plan_id: plan_id, customer_id: customer_id, count: count},
            dataType: 'json',
            success: function(result){
                var $price_block = $('#selling_price');
                var $need_buy_pins = $('#id_need_buy_pins');
                if($need_buy_pins.prop('checked')){
                    if (result['success'] && plan_id && customer_id){
                        $price_block.css('color', 'black').html('$' + result['price']);
                    }
                    else if (!plan_id || !customer_id){
                        $price_block.html('');
                    }
                    else{
                        $price_block.css('color', 'red').html(result['message']);
                    }
                }
                else{
                    $price_block.html('');
                }
            }
        });
    }
    //in case we should immediately go to charge page to create charge
    if (getUrlParameter('with_charge')){
        var form_action = $('.manual-refill-form').attr('action');
        $('.manual-refill-form').attr('action', form_action+'?with_charge=true');
    }
    // Temperately variable for last plan used
    var tmpPlanValue = null,
        disablePurchasingPinFunction = false;
    // Copy to clipboard
    ZeroClipboard.config({
        swfPath: links.ZeroClipboard
    });
    new ZeroClipboard($('#copy_phone_number'));

    // Auto adding unused pin
    (function() {
        var timeout,
            delay = 150;

        $('#id_need_buy_pins')
            .iCheck('update')
            .on('ifChecked', function () {
                $('#id_send_bought_pins')
                    .iCheck('disable')
                    .iCheck('uncheck');
            })
            .on('ifUnchecked', function () {
                $('#id_send_bought_pins')
                    .iCheck('enable')
                    .iCheck('uncheck');
            });

        $('#id_send_bought_pins')
            .iCheck('update')
            .on('ifChecked', function () {
                $('#id_need_buy_pins')
                    .iCheck('disable')
                    .iCheck('uncheck');
            })
            .on('ifUnchecked', function () {
                $('#id_need_buy_pins')
                    .iCheck('enable')
                    .iCheck('uncheck');
            });

        $('#buttons_need_buy_pins_count button')
            .on('mousedown', function () {
                var $this = $(this);
                var $object = $(document.getElementById($this.attr('data-object')));

                if ($object.val().match(/\D+/)) {
                    $object.val(0);
                }

                var action = {
                    inc: function() {
                        if ((+$object.val() + 1) <= 30) {
                            $object.val(+$object.val() + 1);
                        }
                    },
                    dic: function() {
                        if ((+$object.val() - 1) >= 1) {
                            $object.val(+$object.val() - 1);
                        } else {
                            $object.val(1);
                        }
                    }
                };

                switch ($this.attr('action')) {
                    case 'inc':
                        action.inc(true);

                        timeout = setInterval(action.inc, delay);
                        break;
                    case 'dic':
                        action.dic(true);

                        timeout = setInterval(action.dic, delay);
                        break;
                }
            })
            .on('mouseup', function() {
                clearInterval(timeout);
            });

        $('#id_need_buy_pins_count')
            .on('input', function () {
                var $this = $(this);
                $this.val($this.val().replace(/\D+/g, ''));

                if ($this.val()) {
                    $('#id_need_buy_pins').iCheck('enable');
                    if (0 > $this.val()) {
                        $this.val(0);
                    } else
                    if ($this.val() > 30) {
                        $this.val(30);
                    }
                } else {
                    $('#id_need_buy_pins').iCheck('disable');
                }
            });
    })();

    // Initialize selectizes
    // block Customer
    var current_customer = '';
    var $customers = $('#id_customer').selectize({
        sortField: 'text',
        onChange: function (value) {
            current_customer = value;
            update_$phone_number(value);
            if (value != '') {
                $('.edit-customer').attr('href', links.Customer.replace('0', value));
            }
            if (current_customer){
                $.ajax({
                    type: 'GET',
                    url: links.checkCustomerCash.replace('0', current_customer),
                    dataType: 'json',
                    success: function (data) {
                        if ((data['gateway'] == 'CP' || data['gateway'] == 'CA') &&  consts.manualCashAlreadyPaid == 'True'){
                            $('[name="already_paid"]').iCheck('check');
                        }
                        if(data['result'] == true && $('#id_refill_type').val()=='GP'){
                            $('#id_pin').prop('disabled', true);
                            $('#id_need_buy_pins').iCheck('disable').iCheck('uncheck');
                            $('#id_send_bought_pins').iCheck('enable');
                            $('#id_need_buy_pins_count').prop('readonly', false).val(1);
                            $('[data-object="id_need_buy_pins_count"]').prop('disabled', false);
                            $('[name="get_pin_now"]').iCheck('disable').iCheck('uncheck');
                        }
                        else if (data['result'] == true) {
                            $('#id_need_buy_pins, #id_send_bought_pins').iCheck('disable').iCheck('uncheck');
                        }
                        else if ($('#id_refill_type').val()=='GP'){
                            $('#id_pin').prop('disabled', true);
                            $('#id_need_buy_pins, #id_send_bought_pins').iCheck('enable');
                            $('#id_need_buy_pins_count').prop('readonly', false).val(1);
                            $('[data-object="id_need_buy_pins_count"]').prop('disabled', false);
                            $('[name="get_pin_now"]').iCheck('disable').iCheck('uncheck');
                        }
                    }
                });
                var count_of_pins = $('#id_need_buy_pins_count').val();
                if (count_of_pins == 0){
                    count_of_pins = 1;
                }
                getSellingPrice($('#id_plan').val(), value, count_of_pins);
            }
            $.ajax({
                type: 'GET',
                url: '/ajax_customer_getaway_and_last_of_cc/',
                data: {id: value},
                dataType: 'json',
                success: function (data) {
                    if (data['valid']) {
                        var cc = '';
                        if (data['CC']){
                            cc = ' </br><b>Credit card: *<b>' + data['CC']
                        }
                        $('.customer-details').html('<b>Payment Getaway: <b>' + data['getaway'] + cc);
                    }
                }
            });
        },
        onInitialize: function() {
            var that = this;
            GETparam('cid', function() {
                if (this.check()) {
                    if (!this.used()) {
                        that.setValue(this.val());
                        this.used(true);
                    }
                }
            });
        }
    });

    GETparam('crt_from', function() {
        if (this.check()) {
            if (!this.used()) {
                $('#id_already_paid_form_group').remove();
                $('[name="created-from"]').val(this.val());
                this.used(true);
            }
        }
    });

    // block Phone Number
    var $phone_number = $('#id_phone_number').selectize({
        create: function(input) {
                $.ajax({
                    type: 'GET',
                    url: links.ajaxAddPhoneNumber,
                    data: {
                        customer: $('#id_customer').val(),
                        number: input
                    },
                    dataType: 'json',
                    success: function (data) {
                        $('#help_phone_number').text(data)
                    }
                });
            return {
                value: input,
                text: input
            }
        },
        onChange: function(value) {
            $('#copy_phone_number').attr('data-clipboard-text', value);
        },
        onLoad: function() {
            var that = this;

            GETparam('ph', function() {
                if (this.check()) {
                    if (!this.used()) {
                        that.setValue(this.val());
                        this.used(true);
                    }
                } else {
                    var val_ph = $('#hidden_phone_number').val(),
                        val_opt = Object.keys(that.options);

                    that.setValue(val_ph);

                    if (val_opt.length == 1 && !val_ph) {
                        that.setValue(val_opt[0]);
                    }
                }
            });
        }
    });
    function update_$phone_number(value) {
        $.ajax({
            type: 'GET',
            url: links.ajaxPhoneNumber,
            data: {
                id: value
            },
            dataType: 'json',
            success: function(data) {
                var selectize = $phone_number[0].selectize;

                selectize.clear();
                selectize.clearOptions();

                selectize.load(function(callback) {
                    callback(data);
                });
            }
        });
    }

    // block Carriers
    var $carriers = $('#id_carrier').selectize({
        valueField: 'pk',
        labelField: 'name',
        searchField: 'name',
        create: false,
        preload: true,
        render: {
            option: function(item, escape) {
                return '<div>' +
                    '<img src="/static/img/' + escape(item['name_slug']) + '.jpg" style="width:36px;" ><span class="title"> ' + escape(item['name']) + '</span>' +
                    '</div>';
            }
        },
        onChange: update_$plans,
        load: function(query, callback) {
            if(query.length) return callback();

            $.ajax({
                type: 'GET',
                url: links.ajaxCarriers,
                dataType: 'json',
                success: function(data) {
                    callback(data);
                }
            });
        },
        onLoad: function() {
            var that = this;
            var callback = GETparam('carid', function() {
                if (this.check()) {
                    if (!this.used()) {
                        that.setValue(this.val());
                        this.used(true);
                        return true;
                    }
                }
                return false;
            });
            if (!callback) {
                callback = GETparam('lp', function () {
                    //setting last used plan for refill when coming from button Recharge With Last Plan from search tab
                    if (this.check() && !callback) {
                        if (!this.used() && this.val() == 't') {
                            this.used(true);
                            load_last_used_plan();
                            return true;
                        }
                    }
                    return false;
                });
            }
        }
    });

    // block Plans
    var $plans = $('#id_plan').selectize({
        valueField: 'pk',
        labelField: 'id',
        searchField: 'id',
        create: false,
        render: {
            option: function(item, escape) {
                return '<div>' +
                    '<span class="title">' +
                    '<span class="name">' + escape(item.id) + '</span>' +
                    '</span>' +
                    '<span class="description">' + escape(item.name) + '</span>' +
                    '<ul class="meta">' +
                    '<li> Cost: ' + escape(item.cost) + '</li>' +
                    '<li> Type: ' + escape(item.type) + '</li>' +
                    '<li>' + escape(item.available) + ' for use</li>' +
                    '</ul>' +
                    '</div>';
            }
        },
        onChange: function(value) {
            if (this.options[value] && !tmpPlanValue) {
                if (this.options[value]['type'].indexOf('Top-Up') >= 0) {
                    if (!disablePurchasingPinFunction) {
                        $('[value="GP"]').css('display', 'none');
                    }
                    $('#id_refill_type').val('FR').trigger('change');
                    $('#id_pin').prop('readonly', true);
                } else {
                    if (!disablePurchasingPinFunction) {
                        $('[value="GP"]').css('display', 'block');
                    }
                    $('#id_pin').prop('readonly', false);
                }
            }
            var count_of_pins = $('#id_need_buy_pins_count').val();
            if (count_of_pins == 0){
                count_of_pins = 1;
            }
            getSellingPrice(value, $('#id_customer').val(), count_of_pins);
        },
        onLoad: function() {
            var that = this;

            if (tmpPlanValue) {
                this.setValue(tmpPlanValue);
                tmpPlanValue = null;
            } else
            if (
                GETparam('pid', function() {
                    if (this.check()) {
                        if (!this.used()) {
                            that.setValue(this.val());
                            this.used(true);
                            return true;
                        }
                    }
                    return false;
                })
            ) // ======> If true, run the next
                if (
                    GETparam('p', function() {
                        if (this.check()) {
                            if (!this.used()) {
                                $('#id_pin').val(this.val());
                                this.used(true);
                                return true;
                            }
                        }
                        return false;
                    })
                ) // ======> If true, run the next
                    GETparam('rftype', function() {
                        if (this.check()) {
                            if (!this.used()) {
                                $('#id_refill_type').val(this.val()).trigger('change');
                                this.used(true);
                            }
                        }
                    });
        }
    });
    function update_$plans(value) {
        $.ajax({
            type: 'GET',
            url: links.ajaxCarrierPlans,
            data: {
                id: value
            },
            dataType: 'json',
            success: function(data) {
                var selectize = $plans[0].selectize;

                selectize.clear();
                selectize.clearOptions();

                selectize.load(function(callback) {
                    callback(data);
                });
            }
        });
    }

    function load_last_used_plan() {
        $.ajax({
            type: "GET",
            url: links.ajaxLastTransData,
            data: {
                phone_number: $phone_number.val()
            },
            dataType: "json",
            success: function (data) {
                if (data['exist']) {
                    $('#last_used_plan').text('Load last used plan');

                    var selectize_$carriers = $carriers[0].selectize;

                    selectize_$carriers.setValue(data['carrier']);
                    tmpPlanValue = data['plan'];
                    $('#id_refill_type').val(data["refill_type"]).trigger('change');
                    $('#id_pin').trigger('change');
                } else {
                    $('#last_used_plan').text('No transactions for this number');
                }
            }
        });
    }

    // Load last used plan on click
    $('#last_used_plan').on('click', load_last_used_plan);

    // Get local utcOffset (timezone) for datetime_refill
    (function () {
        $('#datetimepicker').datetimepicker({
            minDate: moment(),
            format: "DD MMMM YYYY HH:mm"
        });

        $('[name="datetime_refill_tzone"]').val(moment().utcOffset());
    })();

    // If pin is entered
    (function() {
        $('#id_pin')
            .on('input', function() {
                if (
                    $(this).val() === ''
                ) {
                    $('[value="GP"]').css('display', 'block');
                    $('#id_need_buy_pins_count').val(0);
                    $('#id_need_buy_pins')
                        .iCheck('disable')
                        .iCheck('uncheck');
                } else {
                    if (!disablePurchasingPinFunction) {
                        $('[value="GP"]').css('display', 'none');
                        $('#id_refill_type').val('FR').trigger('change');
                        $('#id_need_buy_pins_count').val(1);
                        $('#id_need_buy_pins')
                            .iCheck('enable');
                    }
                }
            });
    })();

    (function() {
        $('#id_refill_type')
            .on('change', function() {
                switch ($(this).val()) {
                    case 'GP':
                        if (current_customer){
                            $.ajax({
                                type: 'GET',
                                url: links.checkCustomerCash.replace('0', current_customer),
                                dataType: 'json',
                                success: function (data) {
                                    $('#id_pin').prop('disabled', true);
                                    $('#id_need_buy_pins_count').prop('readonly', false).val(1);
                                    if (data['result'] != true) {
                                        $('[data-object="id_need_buy_pins_count"]').prop('disabled', false);
                                        $('#id_send_bought_pins, #id_need_buy_pins').iCheck('enable');
                                        $('[name="get_pin_now"]').iCheck('disable').iCheck('uncheck');
                                    }
                                    else{
                                        $('#id_need_buy_pins')
                                            .iCheck('disable')
                                            .iCheck('uncheck');
                                        $('#id_send_bought_pins').iCheck('enable');
                                        $('[data-object="id_need_buy_pins_count"]').prop('disabled', true);
                                        $('[name="get_pin_now"]').iCheck('disable').iCheck('uncheck');
                                    }
                                }
                            });
                        }
                        break;
                    case 'FR':
                        $('#id_need_buy_pins, #id_send_bought_pins')
                            .iCheck('disable')
                            .iCheck('uncheck');
                        $('#id_pin').prop('disabled', false);
                        $('#id_need_buy_pins_count').prop('readonly', true).val(0);
                        $('[data-object="id_need_buy_pins_count"]').prop('disabled', true);
                        $('[name="get_pin_now"]').iCheck('enable');
                        break;
                }
            })
            .trigger('change');
    })();

    (function() {
        GETparam('paid', function () {
            if (this.check()) {
                if (!this.used() && this.val() === 'true') {
                    $('#div_paid').show();
                    this.used(true);
                }
            }
        });
    })();
    function get_mdn_status(event) {
        if(!$phone_number.val())
        {
            return
        }
        button = $(this);
        button.text('..checking');
        $.ajax({
            type: "GET",
            url: links.ajaxGetExpDate,
            data: {
                phone_number: $phone_number.val(),
                type: 'mdn_status'
            },
            dataType: "json",
            success: function (data) {
                if (data['valid']) {
                    data['mdn_status'] = data['mdn_status'].replace(/<\/?[^>]+>/g,'').replace(new RegExp('\n', 'g'), '<br>');
                    mdn_status = data['mdn_status'];
                    if (!data['url']) {
                    } else {
                        mdn_status = mdn_status +"<a href='"+ data['url'] + "' target='_blank'>Link on page</a>"
                    }
                    $('#exp_date_value').html(mdn_status);
                    if (event.data.with_schedule) {
                        var selectize_$carriers = $carriers[0].selectize;
                        selectize_$carriers.setValue(data['carrier']);

                        if (data['plan']) {
                            tmpPlanValue = data['plan'];
                        }
                        else if (data['message']) {
                            alert(data['message']);
                        }
                        $('#id_renewal_date').datepicker('setDate', data['renewal_date']);
                        schedule = data['schedule'];
                    }
                } else {
                    mdn_status = data['message'].replace(new RegExp('\n', 'g'), '<br>');
                    if(data['message'])
                    {
                        alert(data['message']);
                    }
                    if(data['url'])
                    {
                        mdn_status = mdn_status + "<br><a href='" + data['url'] + "' target='_blank'>Link on page</a>"
                    }
                    if(!mdn_status)
                    {
                        mdn_status = "Not active!";
                    }
                    $('#exp_date_value').html(mdn_status);

                }
            },
            complete: function () {
                if (event.data.with_schedule){
                    name = 'Get results of Carrier & refill with that plan'
                }
                else{
                    name = 'Get results of Carrier'
                }
                button.text(name);
            }
        });
    }
    $('#mdn_button').on('click',{with_schedule: false}, get_mdn_status);
    $('#get_result_from_carrier').on('click',{with_schedule: true}, get_mdn_status);

    $('#id_need_buy_pins_count').on('input', function () {
        var count_of_pins = $('#id_need_buy_pins_count').val();
        if (count_of_pins == 0){
            count_of_pins = 1;
        }
        getSellingPrice($('#id_plan').val(), $('#id_customer').val(), count_of_pins);
    });
    $('#id_need_buy_pins').on('ifChanged', function () {
        var count_of_pins = $('#id_need_buy_pins_count').val();
        if (count_of_pins == 0) {
            count_of_pins = 1;
        }
        getSellingPrice($('#id_plan').val(), $('#id_customer').val(), count_of_pins);
    });
});

function validateForm() {
    var customer = $('#id_customer').val();
    var phone_number = $('#id_phone_number').val();
    var carrier = $('#id_carrier').val();
    var plan = $('#id_plan').val();
    if (!customer || !phone_number || !carrier || !plan){
        $('#submit_button_text').text("Refill Now");
        $('.refill-now').attr("disabled", false);
        return false;
    }
    $('#submit_button_text').text("Form submiting.....");
    $('.refill-now').attr("disabled", true);
    $.ajax({
            type: "GET",
            url: links.ajaxManualDuplication,
            data: {
                pn: phone_number
            },
            success: function (data) {
                if (data['duplicated'] && !getUrlParameter('crt_from')){
                   if (confirm('Their was a transaction for this number in the ' +
                       'last 12 hours. Please do you want to continue?')){
                           $(".manual-refill-form").submit();
                        }
                   else{
                       $('#submit_button_text').text("Refill Now");
                       $('.refill-now').attr("disabled", false);
                       return false;
                   }
                }
                else{
                    $(".manual-refill-form").submit();
                }
            }
        });
    }
    $('#id_pin').on('change', function(){
        $(this).val($(this).val().replace(/\s/g, ''));
    });