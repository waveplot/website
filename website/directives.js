angular.module("waveplot.directives", []).directive('highlightHover', function () {
    return {
        link: function highlightHover(scope, element, attrs) {
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
        link: function highlightSelect(scope, element, attrs) {
            element.on('click', function(){
                element.toggleClass('highlight-select');
            });
        }
    };
}).directive('clickScroll', function () {
    return {
        link: function clickScroll(scope, element, attrs) {
            element.on('click', function(){
                $('html, body').animate({
                    scrollTop: element.offset().top - 50
                }, 1000);
            });
        }
    };
}).directive('fallbackSrc', function () {
//http://stackoverflow.com/questions/16349578/angular-directive-for-a-fallback-image
    return {
        link: function postLink(scope, iElement, iAttrs) {
            iElement.bind("load", function() {
                img = new Image();

                img.src = iAttrs.fallbackSrc;

                img.onload = function() {
                    iElement.attr('src', this.src);
                };
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
                var full = !(element.hasClass("waveplot-preview") || element.hasClass("waveplot-thumb"));

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
}).directive('dateToAgo', function () {
    return {
        scope: {
            dateToAgo: '='
        },
        link: function dateToAgoFunc(scope, element, attrs) {
            var d = new Date(scope.dateToAgo);
            var current = new Date();

            if(d > current) {
                element.text("future");
                return;
            }

            var secs = (current - d)/1000;
            var mins = secs/60;
            var hours = mins/60;

            var diff_string = "";
            var value;

            if(hours < 23.5) {
                if(mins > 59) {
                    value = hours;
                    diff_string = " hour";
                } else if(secs < 60) {
                    value = secs;
                    diff_string = " second";
                } else {
                    value = mins;
                    diff_string = " minute";
                }
            } else {
                var days = hours/24;
                var months = days/30;
                var years = months/12;

                if(months > 11.5) {
                    value = years;
                    diff_string = " year";
                } else if(days < 30) {
                    value = days;
                    diff_string = " day";
                } else {
                    value = months;
                    diff_string = " month";
                }
            }

            value = value.toFixed(0);
            diff_string = value + diff_string + (value > 1 ? "s ago" : " ago");
            element.text(diff_string);
        }
    }
}).directive('barcode', function () {
    return {
        link: function barcode(scope, element, attrs) {
            element.barcode(attrs.barcodeValue, attrs.type, {
                barHeight: attrs.height,
                showHRI: ("barcodeText" in attrs)
            });
        }
    }
});
