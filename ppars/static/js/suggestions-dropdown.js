/**
 * Created by vlaslive on 03.07.15.
 */
$(document).ready(function(){
    $("input#search-input").on('input', function (e) {
        if ($('#search-input').val()){
            $.ajax({
                type: 'GET',
                url: '/ajax_search_dropdown/',
                data: { text: $('#search-input').val() },
                dataType: 'json',
                success: function(result){
                    if (result.length > 0){
                        $('.search-dropdown').html('');
                        for (var i = 0; i < result.length; i++){
                            var name = result[i]["name"];
                            if (result[i]["name"].length>26){
                                name = result[i]["name"].substring(0,24) + "..."
                            }
                            $('.search-dropdown').append("<li><a href=\"/search/?searchfor="+ result[i]["number"]
                            + "\"><div>" + name + "</div><div><b>" + result[i]["number"] + "</b></div></a></li>");
                        }
                        $(".search-dropdown").show();
                        $("#search-input").dropdown("toggle");
                    }
                    else{
                        $(".search-dropdown").hide();
                    }
                }
            });
        }
        else{
            $(".search-dropdown").hide();
        }
    });
});
