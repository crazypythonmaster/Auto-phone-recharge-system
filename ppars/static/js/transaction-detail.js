$(document).ready(function () {
    // Transaction Steps initialize
    var datatable_steps,
        last_updated_steps_count = 0,
        window_blured,
        initialized_page = false;
    (function () {
        datatable_steps = $('#steps').DataTable({
            'columns': [
                {
                    'data': 'created',
                    'title': 'Timestamp'
                },
                {
                    'data': 'operation',
                    'title': 'Step Name'
                },
                {
                    'data': 'action',
                    'title': 'Action'
                },
                {
                    'data': 'status_str',
                    'title': 'Status'
                },
                {
                    'data': 'adv_status',
                    'title': 'Advanced Status'
                }
            ],
            bSort: false,
            sDom: '<"row"<"col-md-4"l><"col-md-8"f>><"table-responsive"t><"row"<"col-md-12"p>>',
            oLanguage:
            {
                sLengthMenu: '\_MENU_',
                sSearch: '',
                sSearchPlaceholder: 'Searching...',
                oPaginate:
                {
                    sPrevious: '<',
                    sNext: '>'
                }
            }
        });
    })();

    // Show loading overlay
    function LoadingOverlay() {
        var $overlay = $('.overlay'),
            $loading = $('.loading-img');

        return {
            show: function () {
                $overlay.show();
                $loading.show();
            },
            hide: function () {
                $overlay.hide();
                $loading.hide();
            }
        };
    }

    // Scheduled monthly
    $('#schedule_monthly').on('click', function () {
        if (payment_gateway_cash)
        {
            $('#confirm_schedule_monthly_minus_one_day').hide();
            $('#confirm_schedule_month').show();
            $("#id_modal_cash").modal();
        }
        else
        {
            ajax_schedule_monthly_with_check();
        }
    });

    $('#confirm_schedule_month').on('click', function () {
        ajax_schedule_monthly_with_check();
    });

    // check on complete before schedule monthly
    function ajax_schedule_monthly_with_check(){
        $.ajax({
            url: links.ajaxCheckManualTransactionEnded,
            success: function (result) {
                if (result['ended']){
                    ajax_schedule_monthly(1);
                }
                else{
                    dialog('Transaction not yet completed do you want to schedule it based on transaction start date?',
                        function() {
                            ajax_schedule_monthly(0);
                        },
                        function() {
                            // Do nothing
                        }
                    );
                }
            }
        });
    }

    // schedule monthly
    function ajax_schedule_monthly(ended)
    {
        $.ajax({
            url: links.ajaxScheduleMonthly,
            data: {minus: 0, ended: ended, transaction_id: g_data.id, type: 'normal'},
            success: function (result) {
                if (result['valid']) {
                    dialog('Scheduler refill created. Do you want to edit it?',
                        function() {
                            window.location = links.autorefill.replace('0', result['id']);
                        },
                        function() {
                            // Do nothing
                        }
                    );
                    updatePage();
                }
                else {
                    alert(result['error']);
                }
            }
        });
    }

    // check on complete before schedule monthly
    $('#schedule_monthly_minus_one_day').on('click', function(){
        if (payment_gateway_cash)
        {
            $('#confirm_schedule_month').hide();
            $('#confirm_schedule_monthly_minus_one_day').show();
            $("#id_modal_cash").modal();
        }
        else
        {
            schedule_monthly_minus_one_day();
        }
    });
    $('#confirm_schedule_monthly_minus_one_day').on('click', function(){
        schedule_monthly_minus_one_day();
    });
   function schedule_monthly_minus_one_day(){
        $.ajax({
            url: links.ajaxCheckManualTransactionEnded,
            success: function (result) {
                if (result['ended']){
                    ajax_schedule_monthly_minus_one(1);
                }
                else{
                    dialog('Transaction not yet completed do you want to schedule it based on transaction start date?',
                        function() {
                            ajax_schedule_monthly_minus_one(0);
                        },
                        function() {
                            // Do nothing
                        }
                    );
                }
            }
        });
    }
    //schedule monthly based on results of carrier
    function schedule_monthly_based_on_results_of_carrier(){
        $('#schedule_monthly_carrier').html('PROCESSING');
        $.ajax({
            url: links.ajaxScheduleMonthly,
            data: {transaction_id: g_data.id, type: 'carrier'},
            success: function (result) {
                if (result['valid']) {
                    dialog('Scheduler refill created. Do you want to edit it?',
                        function() {
                            window.location = links.autorefill.replace('0', result['id']);
                        },
                        function() {
                            // Do nothing
                        }
                    );
                    updatePage();
                } else if(result['error']){
                    alert(result['error']);
                }
            },
            complete: function(){
                $('#schedule_monthly_carrier').html('schedule monthly based<br>on results of carrier');
            }
        });
    }
    $('#schedule_monthly_carrier').on('click', schedule_monthly_based_on_results_of_carrier);
    // schedule monthly
    function ajax_schedule_monthly_minus_one(ended) {
        $.ajax({
            url: links.ajaxScheduleMonthly,
            data: {minus: 1, ended: ended, transaction_id: g_data.id, type: 'normal'},
            success: function (result) {
                if (result['valid']) {
                    dialog('Scheduler refill created. Do you want to edit it?',
                        function() {
                            window.location = links.autorefill.replace('0', result['id']);
                        },
                        function() {
                            // Do nothing
                        }
                    );
                    updatePage();
                } else {
                    alert(result['error']);
                }
            }
        });
    }

    // Mark paid
    $('#markPaid').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'paid'
            },
            success: function() {
                updatePage();
            }
        });
    });

    $('#markRefund').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'refund'
            },
            success: function() {
                updatePage();
            }
        });
    });

    // Mark completed
    $('#markCompleted').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'completed'
            },
            success: function () {
                updatePage();
            }
        });
    });

    // Enter pin and update the next schedule refill date
    // Show input and hide button <id="enterPinAndUpdate">
    $('#enterPinAndUpdate').on('click', function () {
        $('#enterPinAndUpdate-div').show();
        $('#enterPinAndUpdate').hide();
    });

    // Hide pin-input and show button <id="enterPinAndUpdate">
    $('#enterPinAndUpdate-cancel').on('click', function () {
        $('#enterPinAndUpdate-div').hide();
        $('#enterPinAndUpdate').show();
    });

    // Request to server 'Complete with pin'
    $('#enterPinAndUpdate-commit').on('click', function () {
        var $pin_input = $('#enterPinAndUpdate-input');

        if ($pin_input.val().match(/^[0-9]+$/)) {
            LoadingOverlay().show();
            $.ajax({
                url: links.ajaxMarkTransaction,
                data: {
                    button: 'enter_pin_and_update',
                    pin: $pin_input.val()
                },
                success: function () {
                    $('#enterPinAndUpdate-div').hide();
                    $('#enterPinAndUpdate').show();
                    updatePage();
                }
            });
        } else {
            $pin_input.tooltip('show').parent().addClass('has-error');
        }
    });

    // Mark completed with pin
    // Show input and hide buttons with 'markCompleted'
    $('#markCompletedWithPin').on('click', function () {
        $('#pin-enter').show();
        $('#markCompleted, #markCompletedWithPin')
            .hide();
    });

    // Hide pin-input and show buttons with 'markCompleted'
    $('#pin-cancel').on('click', function () {
        $('#markCompleted, #markCompletedWithPin').show();
        $('#pin-enter').hide();
    });

    // Request to server 'Complete with pin'
    $('#pin-commit').on('click', function () {
        var $pin_input = $('#pin-enter-input');

        if ($pin_input.val().match(/^[0-9]+$/)) {
            LoadingOverlay().show();
            $.ajax({
                url: links.ajaxMarkTransaction,
                data: {
                    button: 'completed-with-pin',
                    pin: $pin_input.val()
                },
                success: function () {
                    $('#pin-enter').hide();
                    updatePage();
                }
            });
        } else {
            $pin_input.tooltip('show').parent().addClass('has-error');
        }
    });

    // Close transaction
    $('#closeTrans').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'closed'
            },
            success: function() {
                updatePage();
            }
        });
    });

    // Close transaction and create similar
    $('#closeTransAndCrSim').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'closed'
            },
            success: function() {
                window.location = links.createSimilarTransaction();
            }
        });
    });

    // Create similar transaction
    $('#CrSim').on('click', function () {
        window.location = links.createSimilarTransaction();
    });

    // Restart transaction
    $('#restartTrans').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'restarted'
            },
            success: function () {
                setTimeout(function () {
                    updatePage();
                }, 2000);
            }
        });
    });

    // Restart prerefill
    $('#restartPrerefill').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'prerefill_restart'
            },
            success: function () {
                setTimeout(function () {
                    updatePage();
                }, 2000);
            }
        });
    });

    // Retry charge
    $('#retryCharge').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'retry-charge'
            },
            success: function () {
                setTimeout(function () {
                    updatePage();
                }, 2000);
            }
        });
    });

    // Restart transaction and retry charge
    $('#restartTransAndRetryCharge').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'restart-trns-and-charge'
            },
            success: function () {
                setTimeout(function () {
                    updatePage();
                }, 2000);
            }
        });
    });

    // Retry send message with pins to customer
    $('#retrySendMessageWithPins').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'retry-send-msg-pin'
            },
            success: function () {
                setTimeout(function () {
                    updatePage();
                }, 2000);
            }
        });
    });

    // Send message with pins to customer
    $('#SendMessageWithPins').on('click', function () {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxMarkTransaction,
            data: {
                button : 'send-msg-pin'
            },
            success: function () {
                setTimeout(function () {
                    updatePage();
                }, 2000);
            }
        });
    });

    $('#save_notes').on('click', function(){
        $(this).html('saving...');
        $.ajax({
                url: links.ajaxSaveNote,
                data: {
                    note: $('#id_notes').val()
                },
                success: function (data) {
                    $('#id_notes').val(data['note']);
                },
                complete: function(){
                    $('#save_notes').html('Save Note');
                }
            });
    });

    $('#refreshData').on('click', function () {
        var $this = $(this);

        LoadingOverlay().show();
        $this.button('loading');

        setTimeout(function () {
            updatePage();
            $this.button('reset');
        }, 2000);
    });

    // Updating information
    (function () {
        Updater = (function Updater () {
            var looper;
            var intervalUpdate = 0;
            var userIntervalUpdate = 0;
            var run = false;

            var CheckUpdate = function (option) {
                if (option !== 'not-updated') {
                    updatePage();
                }
                clearInterval(looper);
                if (run) {
                    CheckState();
                    if (intervalUpdate) {
                        looper = setInterval(CheckUpdate, intervalUpdate);
                    }
                }
            };

            var CheckState = function () {
                switch (g_data.state) {
                    case 'P':
                        intervalUpdate = 30000;
                        break;
                    case 'E':
                        intervalUpdate = 0;
                        break;
                    case 'Q':
                        if (userIntervalUpdate) {
                            intervalUpdate = userIntervalUpdate;
                        } else {
                            intervalUpdate = 30000;
                        }
                        break;
                    case 'R':
                        if (g_data.status == 'E' && userIntervalUpdate) {
                            intervalUpdate = userIntervalUpdate;
                        } else {
                            intervalUpdate = 300000;
                        }
                        break;
                    case 'I':
                        intervalUpdate = 0;
                        break;
                    case 'C':
                        intervalUpdate = 0;
                        break;
                    default :
                        intervalUpdate = 0;
                        break;
                }
            };

            return {
                run: function () {
                    run = true;
                    CheckUpdate();
                    return this;
                },
                stop: function () {
                    run = false;
                    CheckUpdate('not-updated');
                    return this;
                },
                interval: function (interval) {
                    userIntervalUpdate = interval;
                    CheckUpdate('not-updated');
                    return this;
                }
            };
        })();
        Updater.run();
    })();

    (function () {
        AnimateTitle = (function AnimateOnHaveUpdate() {
            var looper;
            var run = false;

            var animateTitle = {
                icon: ['[+] ', '[0] '],
                animate: function () {
                    var title = document.title;

                    if (title.indexOf(this.icon[0]) >= 0) {
                        title = title.replace(this.icon[0], run ? this.icon[1] : '');
                    } else
                    if (title.indexOf(this.icon[1]) >= 0) {
                        title = title.replace(this.icon[1], run ? this.icon[0] : '');
                    } else {
                        title = this.icon[0] + title;
                    }

                    document.title = title;
                }
            };

            var Check = function () {
                animateTitle.animate();
                clearInterval(looper);
                if (run) {
                    looper = setInterval(Check, 500);
                }
            };

            return {
                run: function () {
                    run = true;
                    Check();
                    return this;
                },
                stop: function () {
                    run = false;
                    return this;
                }
            };
        })();
    })();
    var plan = '';
    function updatePage() {
        LoadingOverlay().show();
        $.ajax({
            url: links.ajaxTransaction,
            type: 'GET',
            dataType: 'JSON',
            contentType: 'JSON',
            success: function(result) {
                var transaction = result['transaction'];
                var steps = result['steps'];
                // Load information in right panel
                $('#triggered_by').html(transaction['triggered_by']);
                $('#phone_number').html(transaction['phone_number']);
                $('#plan').html(transaction['plan']);
                plan = transaction['plan'];
                $('#profit').html(transaction['profit']);
                $('#refill_type').html(transaction['refill_type']);
                $('#pin').html(ParsePins(transaction['pin']));
                if (transaction['price']){
                    $('#pin').append('$'+Object.keys(transaction['pin']).length*transaction['price']);
                }
                UpdateLinkPins();
                $('#state').html(transaction['state_str']);
                $('#status').html(transaction['status_str']);
                $('#pustatus').html(transaction['charge']);
                if (transaction['charge'] != '' &&
                    !(transaction['state'] == 'C' && transaction['status'] == 'S' && transaction['plan_type'] != 'TP')) {
                    $('#restartTransAndRetryCharge, #retryCharge').show();
                } else {
                    $('#restartTransAndRetryCharge, #retryCharge').hide();
                }
                if (transaction['payment_type'])
                {
                    $('#payment_type').html(transaction['payment_type']);
                    $('#payment_gateway').html(transaction['payment_getaway']);
                }
                if (transaction['state'] == 'R' || transaction['state'] == 'Q') {
                    $('#closeTrans').show();
                    $('#closeTransAndCrSim').show();
                    $('#CrSim').hide();
                } else {
                    $('#closeTrans').hide();
                    $('#closeTransAndCrSim').hide();
                    $('#CrSim').show();
                }
                if (transaction['state'] == 'I' || transaction['state'] == 'C') {
                    $('#restartTrans').show();
                } else {
                    $('#restartTrans').hide();
                }
                if (transaction['state'] == 'C' &&
                    transaction['status'] == 'E' &&
                    transaction['current_step'] != 'recharge_phone' &&
                    transaction['current_step'] != 'send_notifications' &&
                    transaction['autorefill_trigger'] != 'MN') {
                    $('#restartPrerefill').show();
                } else {
                    $('#restartPrerefill').hide();
                }
                if (transaction['paid']) {
                    $('#pstatus-indicator')
                        .removeAttr('class')
                        .addClass('fa fa-check-circle text-success')
                        .show();
                    $('#markPaid')
                        .hide();
                    $('#markRefund')
                        .show();
                } else {
                    $('#pstatus-indicator')
                        .removeAttr('class')
                        .addClass('fa fa-minus-circle text-danger')
                        .show();
                    $('#markPaid')
                        .show();
                    $('#markRefund')
                        .hide();
                }
                if (g_data.company != transaction['company']) {
                    $('#pstatus-indicator')
                        .removeAttr('class')
                        .addClass('fa fa-minus-circle text-danger')
                        .show();
                    $('#markPaid')
                        .hide();
                    $('#markRefund')
                        .hide();
                }
                if (transaction['completed'] == 'R') {
                    $('#tstatus-indicator')
                        .removeAttr('class')
                        .addClass('fa fa-check-circle text-success')
                        .show();
                    $('#markCompleted, #markCompletedWithPin')
                        .hide();
                } else {
                    if (g_data.company != transaction['company']) {
                        $('#tstatus-indicator')
                            .removeAttr('class')
                            .addClass('fa fa-minus-circle text-danger')
                            .show();
                        $('#markCompleted, #markCompletedWithPin')
                            .hide();
                    } else {
                        $('#tstatus-indicator')
                            .removeAttr('class')
                            .addClass('fa fa-minus-circle text-danger')
                            .show();
                        $('#markCompleted, #markCompletedWithPin')
                            .show();
                    }
                }

                if (transaction['status'] == 'E') {
                    $('#status_row').addClass('danger');
                } else {
                    $('#status_row').removeClass('danger');
                }
                if (transaction['adv_status']) {
                    $('#adv_status').html(transaction['adv_status']);
                }
                $('#started').html(transaction['started']);
                if (transaction['state'] == 'C') {
                    $('#ended').html(transaction['ended']);
                }
                if (transaction['eta_update'] != '' || transaction['eta_update'] >= 0) {
                    var interval = +transaction['eta_update'] * 1000 + 2000,
                        maxInt = Math.pow(2,31) - 1;
                    if (interval < maxInt - 1) {
                        Updater.interval(interval);
                    } else {
                        Updater.interval(maxInt - 1);
                    }
                } else {
                    Updater.interval(0);
                }
                //if (!(transaction['plan'].indexOf('PagePlus') > -1))
                //{
                //    $('#exp_date').html('');
                //    $('#exp_date_title').html('');
                //}
                datatable_steps.clear();
                for (var i = 0; i < steps.length; i++) {
                    $(datatable_steps.row.add(steps[i]).node())
                        .addClass(steps[i]['status'] == 'E' ? 'danger' : '');
                }
                if (steps.length != last_updated_steps_count ||
                    g_data.state != transaction['state'] ||
                    g_data.status != transaction['status'] ||
                    g_data.paid != transaction['paid']) {
                    last_updated_steps_count = steps.length;
                    if (initialized_page) {
                        if (window_blured) {
                            AnimateTitle.run();
                        }
                        if (transaction['status'] != 'P') {
                            var sound = document.getElementById('notif-sound');

                            sound.pause();
                            sound.currentTime = 0;
                            sound.play();
                        }
                    }
                    if (!initialized_page) {
                        initialized_page = true;
                    }
                }
                g_data.state = transaction['state'];
                g_data.status = transaction['status'];
                g_data.paid = transaction['paid'];
                datatable_steps.draw().page('last').draw(false);
                LoadingOverlay().hide();
            }
        });
    }

    $(window).on('blur', function() {
        window_blured = true;
    });
    $(window).on('focus', function () {
        window_blured = false;
        AnimateTitle.stop();
    });
    $('#get_exp_date').on('click', function(){
        $(this).text('..checking');
        if ($('#carrier_id'))
        {
            carrier = $('#carrier_id').val()
        }
        else{
            carrier = 0
        }
        $.ajax({
            type: "GET",
            url: links.ajaxGetExpDate,
            data: {
                type: 'mdn_status',
                phone_number: $('#phone_number').html(),
            },
            dataType: "json",
            success: function (data) {
                if (data['valid']) {

                    data['mdn_status'] = data['mdn_status'].replace(/<\/?[^>]+>/g,'');
                    $('#id_notes').val(data['mdn_status']);
                    if (!data['url']) {
                    } else {
                        $('#link_result').html("<a href='" + data['url'] + "' target='_blank'>Link on page</a>");
                    }
                } else {
                    $('#id_notes').text('Not active.');
                }
            },
            complete: function(){
                $('#get_exp_date').text('Get results of Carrier');
            },
            error: function(){
                $('#get_exp_date').text('Error.');
            }
        });
    });
       // Add pin to unused
    function UpdateLinkPins () {
        $('a[action="add_tu"]').on('click', function () {
            var $this = $(this);

            LoadingOverlay().show();

            $.ajax({
                url: links.ajaxAddPinToUnused,
                data: {
                    pin: $this.parent().parent().parent().find('button').text()
                },
                success: function () {
                    updatePage();
                }
            });
        });
    }

    function ParsePins(pins) {
        var html = '';

        for (var pin in pins) {
            html += '<div class="dropdown inline">' +
            '<button class="btn btn-success btn-xs dropdown-toggle" type="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' +
            pin + '</button>' +
            '<ul class="dropdown-menu dropdown-menu-right">';

            if (pins[pin]['receipt'] != '') {
                html += '<li><a href="' + pins[pin]['receipt'] + '" target="_blank">Receipt</a></li>';
            }

            if (pins[pin]['unus_pin'] != '') {
                html += '<li><a href="' + pins[pin]['unus_pin'] + '" target="_blank">Unused link</a></li>';
            } else {
                html += '<li><a href="#" action="add_tu">Add to unused</a></li>';
            }

            html += '</ul>';
            html += '</div> ';
        }

        return html;
    }

});

