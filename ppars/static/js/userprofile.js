$(document).ready(function () {
    // defaults values
    var send_pin_prerefill = {
        status: $('[name="send_pin_prerefill"]').val()
    };

    function CheckToApply() {
        $('#send_pin_prerefill-apply').prop('disabled',
            $('[name="send_pin_prerefill"]').val() == send_pin_prerefill.status
        );
    }

    // change send_pin_prerefill by mirror
    $('[name="send_pin_prerefill"]').on('change', function() {
        CheckToApply();
    });

    // Send ajax
    $('#send_pin_prerefill-apply').click(function() {
        var $this = $(this);

        $('[name="send_pin_prerefill"]').attr('disabled', '');

        $this
            .text('Applying...')
            .attr('disabled', '');
        $.get($this.attr('href'), {
            send_pin_prerefill: $('[name="send_pin_prerefill"]').val()
        }, function() {
            $('[name="send_pin_prerefill"]').removeAttr('disabled');
            $this.text('Apply');
            send_pin_prerefill ={
                status: $('[name="send_pin_prerefill"]').val()
            }
        });
    });

    //Send ajax set default notification method
    $('#set_default_notification').click(function(){
        var $this = $(this);
        $.get($this.attr('href'),{

        }, function(){
            $this.addClass('disabled');
        })
    });
});