angular.module("waveplot.directives", []).directive('highlightHover', function () {
    return {
        link: function highlight(scope, element, attrs) {
            element.on('mouseenter', function(){
				if(scope.selected[element.attr('id')] != true){
					element.css('background-color','#e0e0e0');
				}
            });
            
            element.on('mouseleave', function(){
				if(scope.selected[element.attr('id')] != true){
					element.css('background-color','transparent');
				}
            });
        }
    };
}).directive('highlightSelect', function () {
    return {
        link: function highlight(scope, element, attrs) {
			scope.selected[element.attr('id')] = (attrs['selected'] !== undefined);
			
			if(scope.selected[element.attr('id')]){
				element.css('background-color','#d0d0d0');
			}
			
            element.on('click', function(){
				scope.selected[element.attr('id')] = !scope.selected[element.attr('id')];
				element.css('background-color','#d0d0d0');
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
