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

function drawWavePlot(canvas, waveplot_data) {
    waveplot_data = decodeBase64(waveplot_data);
    canvas.width = waveplot_data.length;
    var centre = canvas.height / 2; //Assume height already set: 21-thumb, 151-preview, 401-actual

    var ctx = canvas.getContext("2d");

    //Fill with white.
    ctx.strokeStyle="#FFFFFF";
    ctx.fillStyle="#FFFFFF";
    ctx.fillRect(0,0,canvas.width,canvas.height);

    ctx.translate(0.0,0.5);

    //Render horizontal lines if full-size
    if(canvas.height == 401) {
        ctx.strokeStyle="#FFBA58";

        ctx.beginPath();
        for(var i = 20; i != 200; i += 20) {
            ctx.moveTo(-1,centre+i);
            ctx.lineTo(canvas.width,centre+i);

            ctx.moveTo(-1,centre-i);
            ctx.lineTo(canvas.width,centre-i);
        }

        ctx.stroke();
    }

    ctx.strokeStyle="#736DAB";

    ctx.beginPath();

    ctx.moveTo(0,centre);
    ctx.lineTo(canvas.width,centre);
    ctx.stroke();

    ctx.setTransform(1,0,0,1,0.5,0);

    //Draw trim points if full size.
    if(canvas.height == 401) {
        ctx.strokeStyle="#FFBA58";

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
    }

    ctx.beginPath();
    for(var i = 0; i != waveplot_data.length; i++)
    {
        var pixel_height = waveplot_data.charCodeAt(i);

        ctx.moveTo(i,centre - pixel_height);
        ctx.lineTo(i,centre + pixel_height + 1);
    }
    ctx.stroke();

    //Draw tick marks if full-size.
    if(canvas.height == 401){
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
}
