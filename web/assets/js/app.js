angular.module('waveplot', ['ui.bootstrap', 'pascalprecht.translate', 'infinite-scroll']).
    config(['$routeProvider','$locationProvider','$translateProvider', '$translatePartialLoaderProvider', function($routeProvider,$locationProvider,$translateProvider, $translatePartialLoaderProvider) {
            $routeProvider.
                when('/waveplot/:uuid', {templateUrl: '/partials/waveplot_uuid.html', controller: WavePlotUUIDCtrl}).
                when('/recording/:mbid', {templateUrl: '/partials/recording_mbid.html', controller: RecordingMBIDCtrl});

            $routeProvider.
                when('/list/waveplot', {templateUrl: '/partials/waveplot_list.html', controller: WavePlotListCtrl}).
                when('/list/recording', {templateUrl: '/partials/recording_list.html', controller: RecordingListCtrl});

            $routeProvider.
                when('/help', {templateUrl: '/partials/help.html', controller: HelpCtrl, resolve: HelpCtrl.resolve}).
                when('/downloads', {templateUrl: '/partials/downloads.html', controller: DownloadsCtrl, resolve: DownloadsCtrl.resolve}).
                when('/get-started', {templateUrl: '/partials/get_started.html'}).
                when('/extreme-dr', {templateUrl: '/partials/extreme_dr.html', controller: ExtremeDRCtrl}).
                when('/register', {templateUrl: '/partials/register.html', controller: RegisterCtrl}).
                when('/activate/:key', {templateUrl: '/partials/activate.html', controller: ActivateCtrl}).
                when('/browse/release', {templateUrl: '/partials/browse_release.html', controller: BrowseReleases}).
                otherwise({redirectTo: '', templateUrl: '/partials/home.html', controller: HomeCtrl, resolve: HomeCtrl.resolve});

            $locationProvider.html5Mode(true).hashPrefix('!');

            $translateProvider.translations('en', {
                "help":"Help",
                "downloads":"Downloads",
                "browse": {
                    "top":"Browse",
                    "artists":"Artists",
                    "albums":"Albums",
                    "songs":"Songs",
                    "dynamic-range":"Dynamic Range"
                }
            });


            $translateProvider.useLoader('$translatePartialLoader', {
              urlTemplate: '/i18n/{part}/{lang}.json'
            });

            $translateProvider.preferredLanguage('en');
        }
    ]
).directive('draw', function() {
    return {
        restrict: 'A',
        link:function(scope, element, attrs) {
            scope.$watch('element', function(val) {
                drawWavePlot(element.get()[0],val.data);
            }, true);
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
}).directive('highlightHover', function () {
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

function MainCtrl($scope, $location, $translate, $translatePartialLoader) {

    $translatePartialLoader.addPart('common');

    $scope.navigation = [
        {"id":0, "url":"/"},
        {"id":1, "url":"/help"},
        {"id":2, "url":"/browse/artist"},
        {"id":3, "url":"/browse/release"},
        {"id":4, "url":"/downloads"}
    ]

    $scope.getNavClass = function(id) {
        if($scope.current_page === id) {
            return "active";
        } else {
            return "";
        }
    }

    $scope.changeLanguage = function (key) {
        $translate.uses(key);
    };

    $scope.current_page = null;

    $scope.setRoute = function (id) {
        if($scope.current_page.id != id) {
            $location.path($scope.navigation[id].url);
            $scope.current_page = id;
        }
    };

   var path = $location.path();
   if(path == "") path = "/";
   for(var i = 0; i != $scope.navigation.length; i++){
      if($scope.navigation[i].url == path){
         $scope.current_page = i;
         break;
      }
   }


}
