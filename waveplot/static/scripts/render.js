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

function drawWavePlot(c, waveplot_data) {
    var ctx=c.getContext("2d");
    c.width = waveplot_data.length;
    c.height = 401;
    var centre = 200;

    console.log("Min: " + Math.min(waveplot_data.length,parseInt($("#render").css("width"))));
    $("#render").css("width", Math.min(waveplot_data.length,parseInt($("#render").css("width"))));

    ctx.strokeStyle="#FFFFFF";
    ctx.fillStyle="#FFFFFF";
    ctx.fillRect(0,0,c.width,401);

    ctx.translate(0.0,0.5);

    ctx.strokeStyle="#FFBA58";

    ctx.beginPath();
    for(var i = 20; i != 200; i += 20) {
        ctx.moveTo(-1,centre+i);
        ctx.lineTo(c.width,centre+i);

        ctx.moveTo(-1,centre-i);
        ctx.lineTo(c.width,centre-i);
    }

    ctx.stroke();

    ctx.strokeStyle="#736DAB";

    ctx.beginPath();

    ctx.moveTo(0,centre);
    ctx.lineTo(c.width,centre);
    ctx.stroke();

    ctx.strokeStyle="#FFBA58";

    ctx.setTransform(1,0,0,1,0.5,0);

    ctx.beginPath();
    for(var i = 0; i != waveplot_data.length; i++) {
        if(waveplot_data.charCodeAt(i) > 10) {
            ctx.moveTo(i,0);
            ctx.lineTo(i,400);
            break;
        }
    }

    for(var i = waveplot_data.length - 1; i >= 0; i--) {
        if(waveplot_data.charCodeAt(i) > 10) {
            ctx.moveTo(i,0);
            ctx.lineTo(i,400);
            break;
        }
    }
    ctx.stroke();

    ctx.strokeStyle="#736DAB";
    ctx.beginPath();
    for(var i = 0; i != waveplot_data.length; i++)
    {
        var pixel_height = waveplot_data.charCodeAt(i);

        ctx.moveTo(i,centre - pixel_height);
        ctx.lineTo(i,centre + pixel_height + 1);
    }
    ctx.stroke();

    ctx.strokeStyle="#000000";
    ctx.beginPath();
    for(var i = 20, j = 1; i < waveplot_data.length; i += 20, j++)
    {
        if(j == 12) {
            j = 0;
            ctx.moveTo(i,centre - 2);
            ctx.lineTo(i,centre + 3);
        } else {
            ctx.moveTo(i,centre);
            ctx.lineTo(i,centre + 1);
        }
    }
    ctx.stroke();

}

$(document).ready(function() {

    var wp=document.getElementById("waveplot");

    var data_path = "http://pi.ockmore.net:19048" + $("#waveplot").attr("data_path");

    $.ajax({
        url: data_path,
        dataType: 'text',
        success: function(result) {
            var img_data = atob(result);

            drawWavePlot(wp,img_data);
        },
        error: function( jqXHR, textStatus, errorThrown) {
            console.log(textStatus);
        }
    });
});
