/* This code overrides the one from mce_filebrowser app to set height=400px */

function mce_filebrowser(field_name, url, type, win) {
    tinyMCE.activeEditor.windowManager.open({
        url: "/mce_filebrowser/" + type + "/",
        width: 400,
        height: 400,
        movable: true,
        inline: true,
        close_previous: "no"
    }, {
        window : win,
        input : field_name
    });  
}
