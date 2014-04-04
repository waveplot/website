angular.module("waveplot.directives", []).directive('highlightHover', function () {
    return {
        link: function highlight(scope, element, attrs) {
            element.on('mouseenter', function(){
                element.addClass('highlight-hover');
            });

            element.on('mouseleave', function(){
                element.removeClass('highlight-hover');
            });
        }
    };
}).directive('highlightSelect', function () {
    return {
        link: function highlight(scope, element, attrs) {
            element.on('click', function(){
                element.toggleClass('highlight-select');
            });
        }
    };
}).directive('clickScroll', function () {
    return {
        link: function highlight(scope, element, attrs) {
            element.on('click', function(){
                $('html, body').animate({
                    scrollTop: element.offset().top - 50
                }, 1000);
            });
        }
    };
}).directive('waveplot', function () {
    return {
        scope: {
            data: '='
        },
        link: function render(scope, element, attrs) {
            scope.$watch('data', function(val , prev) {
                if(val == prev)
                    return;

                var full = !element.hasClass("waveplot-preview");

                raw_data = atob(val);

                element.attr('width', raw_data.length);
                var w = raw_data.length;
                var h = element.attr('height');

                var centre = h / 2; //Assume height already set: 21-thumb, 151-preview, 401-actual

                var ctx = element.get()[0].getContext("2d");

                //Fill with white.
                ctx.strokeStyle="#FFFFFF";
                ctx.fillStyle="#FFFFFF";
                ctx.fillRect(0,0,w,h);

                ctx.translate(0.0,0.5);

                //Render horizontal lines if full-size
                if(full == true) {
                    ctx.strokeStyle="#FFBA58";

                    ctx.beginPath();
                    for(var i = 20; i != 200; i += 20) {
                        ctx.moveTo(-1,centre+i);
                        ctx.lineTo(w,centre+i);

                        ctx.moveTo(-1,centre-i);
                        ctx.lineTo(w,centre-i);
                    }

                    ctx.stroke();
                }

                ctx.strokeStyle="#736DAB";

                ctx.beginPath();

                ctx.moveTo(0,centre);
                ctx.lineTo(w,centre);
                ctx.stroke();

                ctx.setTransform(1,0,0,1,0.5,0);

                //Draw trim points if full size.
                if(full == true) {
                    ctx.strokeStyle="#FFBA58";

                    ctx.beginPath();
                    for(var i = 0; i != raw_data.length; i++) {
                        if(raw_data.charCodeAt(i) > 10) {
                            ctx.moveTo(i,0);
                            ctx.lineTo(i,400);
                            break;
                        }
                    }

                    for(var i = raw_data.length - 1; i >= 0; i--) {
                        if(raw_data.charCodeAt(i) > 10) {
                            ctx.moveTo(i,0);
                            ctx.lineTo(i,400);
                            break;
                        }
                    }
                    ctx.stroke();

                    ctx.strokeStyle="#736DAB";
                }

                ctx.beginPath();
                for(var i = 0; i != raw_data.length; i++)
                {
                    var pixel_height = raw_data.charCodeAt(i);

                    ctx.moveTo(i,centre - pixel_height);
                    ctx.lineTo(i,centre + pixel_height + 1);
                }
                ctx.stroke();

                //Draw tick marks if full-size.
                if(full == true){
                    ctx.strokeStyle="#000000";
                    ctx.beginPath();
                    for(var i = 20, j = 1; i < raw_data.length; i += 20, j++)
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
            });
        }
    };
});
