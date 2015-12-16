/**
 * Created by eugene on 19.06.15.
 */
var schedule ='';
$(document).ready(function() {
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
    /*
    * Fix bug, when initializing page,
    * call event onChange by selectize (Carrier) on loading and selecting default data
    */
    var onInitializingCarriers = true;
    /*
    *
    */

    // Set up datepicker
    $('.date-picker .input-group.date').datepicker({
        startDate: 'today',
        format: 'mm/dd/yyyy',
        todayBtn: 'linked',
        onSelect: function(d,i){
              if(d !== i.lastVal){
                  $(this).change();
              }
         },
    });

    $('.submit-scheduled-refill').on('click', function(){
        $.ajax({
            type: 'GET',
            data: {phone: $phone_number.val(), id: scheduled_refill_id},
            url: links.ajaxCheckForSimilarScheduledRefill,
            success: function (data) {
                if (data['similar']){
                    dialog('A schedule refill for this number already exist ' + data['message'] + ' do you want to continue?',
                        function() {
                            $('.scheduled-refill-form').submit();
                        },
                        function() {
                            // Do nothing
                        }
                    );
                }
                else{
                    $('.scheduled-refill-form').submit();
                }
            }
        });
    });
    if($('#id_renewal_end_date').val()){
        $('#end_date_div').addClass('has-error');
        $('.help-renewal_end_date').html('<p class="text-center">ended due to end date</p>');
    }
    else{
        $('#end_date_div').removeClass('has-error');
        $('.help-renewal_end_date').html('');
    }
    $('#id_renewal_end_date').change(function() {
        if ($('#id_renewal_end_date').val()) {
            $('#end_date_div').addClass('has-error');
            $('.help-renewal_end_date').html('<p class="text-center">ended due to end date</p>');
        }
        else {
            $('#end_date_div').removeClass('has-error');
            $('.help-renewal_end_date').html('');
        }
    });

    // Skip Next Refill
    $('#skip_next_refill').on('click', function() {
        var $this = $(this);

        $.ajax({
            type: 'GET',
            url: links.ajaxSkipNextRefill,
            data: {customer : $('#id_customer').val(),
                phone_number : $('#id_phone_number').val(),
                carrier: $('#id_carrier').val(),
                plan: $('#id_plan').val(),
                renewal_date: $('#id_renewal_date').val(),
                renewal_end_date: $('#id_renewal_end_date').val(),
                renewal_interval: $('#id_renewal_interval').val(),
                schedule: $('#id_schedule').val(),
                notes: $('#id_notes').val(),
                enabled: $('#id_enabled').is(':checked'),
                pre_refill_sms: $('#id_pre_refill_sms').is(':checked'),
                pre_refill_sms_number: $('#id_pre_refill_sms_number').val(),
                need_buy_pins: $('#id_need_buy_pins').is(':checked')
            },
            success: function (data) {

                if (data['valid']){
                    alert('Success! Next refill will be skipped.')
                    $('#id_renewal_date').datepicker('setDate', data['renewal_date']);
                    $('#id_renewal_end_date').datepicker('setDate', data['end_renewal_date']);
                }
            }
        });

    });

    // Tooltip on 'Schedule'
    $('[data-toggle="popover"]').popover({
        trigger: 'manual',
        animate: false
    });
    $('.schedule_select').on('change', function() {
        var $select = $(this),
            msg = 'Select schedule';

        switch($select.val()) {
            case 'MN':
                msg = 'Used for Red Pocket & Page Plus';
                break;
            case 'MD':
                msg = 'Used for rtr';
                break;
            case '1201AM':
                msg = 'Used for Red Pocket when second bucket is enabled';
                break;
        }

        $select.attr('data-content', msg);
        $('[data-toggle="popover"]').popover('show');
    });

    // Enabled / Disabled SMS-number by checkbox
    $('#id_pre_refill_sms')
        .on('ifChecked', function() {
            $('#id_pre_refill_sms_number').prop('disabled', false);
        })
        .on('ifUnchecked', function() {
            $('#id_pre_refill_sms_number').prop('disabled', true);
        });

    $('#id_enabled').on('ifUnchecked', function(){
        if (has_pin_intermediate_step)
        {
            if(!confirm(has_pin_intermediate_step))
            {
                $('#id_enabled')._addAttributes('checked');
            }
        }
    });

    // Validate sms-number
    $('#id_pre_refill_sms_number')
        .on('input', function() {
            this.setCustomValidity(
              $(this).val().match(/^[0-9]{10,10}$/) ?
                  '' : 'The number should only consist of 10 digits!'
            );
        })
        .on('keypress', function(event) {
            var $this = $(this);

            if ($this.val().length > 10) {
                event.preventDefault();
            }
        });

    // Temperately variable for last plan used
    var tmpPlanValue = null;
    // Copy to clipboard
    ZeroClipboard.config({
        swfPath: links.ZeroClipboard
    });
    new ZeroClipboard($('#copy_phone_number'));

    // Initialize selectizes
    // block Customer
    $('#id_customer').selectize({
        sortField: 'text',
        onChange: function (value) {
            update_$phone_number(value);
            if (value != '') {
                $('#link-to-customer').attr('href', links.Customer.replace('0', value));
                $('#link-to-customer').prop('disabled', false);
            } else {
                $('#link-to-customer').prop('disabled', true);
            }
            getSellingPrice($('#id_plan').val(), value, 1);
        },
        onInitialize: function() {
            var that = this;
            var callback = GETparam('cid', function() {
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
                this.setValue($('#hidden_customer').val());
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
            var callback = GETparam('ph', function() {
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
                that.setValue($('#hidden_phone_number').val());
            }
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

    GETparam('crt_from', function() {
        if (this.check()) {
            if (!this.used()) {
                $('#id_notes').val('Schedule created from transaction ' + this.val());
                this.used(true);
            }
        }
    });

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
        onChange: function(value) {
            update_$plans(value);
            if (!onInitializingCarriers) {
                $.ajax({
                    url: links.ajaxCarrier,
                    type: 'GET',
                    dataType: 'JSON',
                    data: {
                        'carid': value
                    },
                    success: function (rs) {
                        $('#id_schedule').val(rs['default_time']);
                    }
                });
            }
        },
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
            if (!callback) {
                this.setValue($('#hidden_carrier').val());
            }
            onInitializingCarriers = false;
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
                    $('#id_need_buy_pins').iCheck('disable').iCheck('uncheck');
                    $('#id_need_buy_pins_label').tooltip('enable');
                } else {
                    $('#id_need_buy_pins').iCheck('enable');
                    $('#id_need_buy_pins_label').tooltip('disable');
                }
            }
            getSellingPrice(value, $('#id_customer').val(), 1);
        },
        onLoad: function() {
            var that = this;
            var callback = false;

            if (tmpPlanValue) {
                this.setValue(tmpPlanValue);
                tmpPlanValue = null;
            } else
            if (
                callback = GETparam('pid', function() { /* START: GETparam */
                    if (this.check()) {
                        if (!this.used()) {
                            that.setValue(this.val());
                            this.used(true);
                            return true;
                        }
                    }
                    return false;
                }) /* END: GETparam */
            ) {
                GETparam('sched', function() {
                    if (this.check()) {
                        if (!this.used()) {
                            if(schedule){
                            $('#id_schedule').val(schedule);
                                schedule='';
                            }else{
                                $('#id_schedule').val(this.val());
                            }
                            this.used(true);
                        }
                    }
                });
                GETparam('ppsms', function() {
                    if (this.check()) {
                        if (!this.used()) {
                            $('#id_pre_refill_sms').val(this.val());
                            this.used(true);
                        }
                    }
                });
                GETparam('ppsmsn', function() {
                    if (this.check()) {
                        if (!this.used()) {
                            $('#id_pre_refill_sms_number').val(this.val());
                            this.used(true);
                        }
                    }
                });
            } else
            if (!callback) {
                this.setValue($('#hidden_plan').val());
            }
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
                if(schedule){
                    $('#id_schedule').val(schedule);
                    schedule = '';
                }
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
                } else {
                    $('#last_used_plan').text('No transactions for this number');
                }
            }
        });
    }
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
                carrier_id: $('#hidden_carrier').val(),
                type: 'mdn_status'
            },
            dataType: "json",
            success: function (data) {
                if (data['valid']) {
                    data['mdn_status'] = data['mdn_status'].replace(/<\/?[^>]+>/g,'').replace(new RegExp('\n', 'g'), '<br>');
                    mdn_status = data['mdn_status'];
                    if (!data['url']) {
                    } else {
                        mdn_status = mdn_status + "<a href='" + data['url'] + "' target='_blank'>Link on page</a>"
                    }
                    $('#exp_date_value').html(mdn_status);
                    if (event.data.with_schedule) {
                        var selectize_carriers = $carriers[0].selectize;
                        selectize_carriers.setValue(data['carrier']);
                        if (data['plan']) {
                            tmpPlanValue = data['plan'];
                        }
                        else if (data['message']) {
                            alert(data['message']);
                        }
                        $('#id_renewal_date').datepicker('setDate', data['renewal_date']);
                        schedule = data['schedule'];
                        if (!(data['plan'] && data['renewal_date'])) {
                        } else {
                            $('.submit-scheduled-refill').click();
                        }
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
                    name = 'Get results of Carrier & Schedule'
                }
                else{
                    name = 'Get results of Carrier'
                }
                button.text(name);
            }
        });
    }
    // Load last used plan on click
    $('#mdn_button').on('click',{with_schedule: false}, get_mdn_status);
    $('#get_plan').on('click',{with_schedule: true}, get_mdn_status);
    $('#last_used_plan').on('click', load_last_used_plan);

    $('#id_need_buy_pins').on('ifChanged', function () {
        getSellingPrice($('#id_plan').val(), $('#id_customer').val(), 1);
    });
});