function showDemo(){
    $("#demo").show();
    $("#doc").hide();

    $("#demoLi").addClass("active");
    $("#docLi").removeClass("active");
}

function showDoc() {
    $("#doc").show();
    $("#demo").hide();

    $("#docLi").addClass("active");
    $("#demoLi").removeClass("active");
}

function submitQuery() {
    file = $("#file").get(0).files[0];
    //alert(file.size);
    alert(file.name);
    // TODO validate file size

    // TODO send the requrest
    // http://stackoverflow.com/questions/166221/how-can-i-upload-files-asynchronously
}

$(function () {
    showDemo();
});
