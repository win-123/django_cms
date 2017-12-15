/**
 * Created by alex on 11/24/16.
 */

//run this script before submit,to make sure all chosen options all selected
function CheckSelectedOptions() {
    // 判断 class 中 有datetime 并且通过索引取值从新赋值
    var inputs = $("input.datetime");
    inputs.each(function (index, ele) {

        if(index%2==0){
            if (inputs[index].value ){
                var datetime_val = inputs[index].value + " " + inputs[index+1].value + ":00.000000";

                inputs[index].value = datetime_val;
            }

        }
    });

    $("select[data-type='m2m_chosen'] option").prop("selected",true);

    RemoveDisabledAttrs();
    //return false;
}


function RemoveDisabledAttrs() {
    $("input").removeAttr("disabled");
    $("select").removeAttr("disabled");
    $("textarea").removeAttr("disabled");
}



function  PostAndAddAnother() {
    console.log($("form"));
    var add_new_ele = "<input type='text' name='_add_another' hidden>";
    $("form").append(add_new_ele);

}