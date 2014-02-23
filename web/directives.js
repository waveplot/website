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
});
