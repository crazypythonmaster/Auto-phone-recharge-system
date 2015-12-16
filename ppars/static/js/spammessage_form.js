$(document).ready(function () {
    // block Carriers
    var onInitializingCarriers = true;
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
                this.setValue($('#hidden_carrier').val());
            }
            onInitializingCarriers = false;
        },
        onChange: function(value) {
            console.log('Hello' + value);
            $('#hidden_carrier').val(value);
        },
    });
    separator = 140;
    $('.tooltip-activate').tooltip();
    $('#__notification ul').css('display', 'block');
    $('#__notification').addClass("active");
    $('#__bulk').addClass("active");
    $('#id_send_with').on('change', function () {
        if ($(this).val() != 'EM')
        {
            $('#information_table').show();
        }
        else
        {
            $('#information_table').hide();
        }
    });
    $('#id_message').on('keyup change', function(){
        var text = $(this).val();
        if (text.length <= 140)
        {
            separator = 140;
        }
        else
        {
            separator = 137;
        }
        $('#messages').html(Math.ceil(text.length/separator));
        $('#charcters').html(separator - (text.length - Math.floor(text.length/separator) * separator));
        $('#amount').html(text.length);
    });
    $('#id_modal_btn').on('click', function(){
        var text = $('#id_message').val(), html = '', messages = Math.ceil(text.length/separator), information='';
        for(var i= 0, beginSlice = 0, separator_local=separator; i<messages;i++) {
            if (messages == 1)
            {
                information='';
            }
            else
            {
                information = (i+1) + "/" + messages;
            }
            if(i+1<messages)
            {
                html = html + "<h4>Part " + (i+1) +
                    "</h4><textarea rows='4' class='form-control tooltip-activate' readonly>" + information
                    + text.slice(beginSlice, separator_local) + "</textarea>";
                beginSlice = separator_local;
                separator_local = separator_local + separator;
            }
            else
            {
                html = html + "<h4>Part " + (i+1) +
                    "</h4><textarea rows='4' class='form-control tooltip-activate' readonly>" +
                   information +
                    text.slice(beginSlice, text.length) + "</textarea>";

            }

        }
        $('#modal-body').html(html);
    });
    });