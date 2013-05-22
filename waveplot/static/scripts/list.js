decodeBase64 = function(s) {
    var e={},i,b=0,c,x,l=0,a,r='',w=String.fromCharCode,L=s.length;
    var A="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    for(i=0;i<64;i++){e[A.charAt(i)]=i;}
    for(x=0;x<L;x++){
        c=e[s.charAt(x)];b=(b<<6)+c;l+=6;
        while(l>=8){((a=(b>>>(l-=8))&0xff)||(x<(L-2)))&&(r+=w(a));}
    }
    return r;
};

function drawThumb(c, waveplot_data) {
    var ctx=c.getContext("2d");
    c.width = waveplot_data.length;
    c.height = 21;
    var centre = 10;

    if(c.width < 50) {
        $("#thCanvas").css("width",c.width);
    }

    ctx.translate(0.0,0.5);

    ctx.strokeStyle="#736DAB";

    ctx.beginPath();

    ctx.moveTo(0,centre);
    ctx.lineTo(c.width,centre);

    ctx.setTransform(1,0,0,1,0.5,0);

    for(var i = 0; i != waveplot_data.length; i++)
    {
        var pixel_height = waveplot_data.charCodeAt(i);
        ctx.moveTo(i,centre - pixel_height);
        ctx.lineTo(i,centre + pixel_height + 1);
    }
    ctx.stroke();
}


$(document).ready(function() {

    var canvases = document.getElementsByClassName("thumb_canvas");

    for(var i = 0; i != canvases.length; i++) {

        //var data_path = "http://pi.ockmore.net:19048" + canvases[i].getAttribute("data_path");
        var data_path = canvases[i].getAttribute("data_path");

        $.ajax({
            url: data_path,
            context: canvases[i],
            dataType: 'text',
            success: function(result) {
                var img_data = atob(result);

                drawThumb(this,img_data);
            },
            error: function( jqXHR, textStatus, errorThrown) {
                console.log(textStatus);
            }
        });
    }
});
