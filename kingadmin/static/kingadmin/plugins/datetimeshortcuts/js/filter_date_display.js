/**
 * Created by lisa on 17/9/28.
 */


$(document).ready(function () {

    var inputs = $("input.datetime");

    inputs.each(function (index, ele) {

        if(index%2==0){

            var display_datetime = inputs[index].value.split(" ");
            inputs[index].value = display_datetime[0];
            var display_time = display_datetime[1].split(":");
            inputs[index+1].value = display_time[0] + ":" + display_time[1];
            if (display_time[0] == ""){
                inputs[index+1].value = ""
            }
        }
    });

});



