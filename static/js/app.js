angular.module('waveplot', ['ui.bootstrap']).
    config(['$routeProvider','$locationProvider', function($routeProvider,$locationProvider) {
            $routeProvider.
                when('/waveplot/:uuid', {templateUrl: 'partials/waveplot_uuid.html', controller: WavePlotUUIDCtrl}).
                when('/recording/:mbid', {templateUrl: 'partials/recording_mbid.html', controller: RecordingMBIDCtrl});

            $routeProvider.
                when('/list/waveplot', {templateUrl: 'partials/waveplot_list.html', controller: WavePlotListCtrl}).
                when('/list/recording', {templateUrl: 'partials/recording_list.html', controller: RecordingListCtrl});

            $routeProvider.
                when('/get-started', {templateUrl: 'partials/get_started.html'}).
                when('/extreme-dr', {templateUrl: 'partials/extreme_dr.html', controller: ExtremeDRCtrl}).
                when('/register', {templateUrl: 'partials/register.html', controller: RegisterCtrl}).
                when('/activate/:key', {templateUrl: 'partials/activate.html', controller: ActivateCtrl}).
                otherwise({redirectTo: '', templateUrl: 'partials/home.html'});

            //$locationProvider.html5Mode(true).hashPrefix('!');
        }
    ]).directive('draw', function() {
        return {
            restrict: 'A',
            link:function(scope, element, attrs) {
                scope.$watch('element', function(val) {
                    drawWavePlot(element.get()[0],val.data);
                }, true);
            }
        }
    }
);

function MainCtrl($scope, $location) {
    $scope.navlinks = [
      { "id":0, "title":"Home", "url":"/", "active":"" },
      { "id":1, "title":"List WavePlots", "url":"/list/waveplot", "active":"" },
     { "id":2, "title":"Recordings with Multiple Waveplots", "url":"/list/recording", "active":"" },
     { "id":3, "title":"Extreme D.R.", "url":"/extreme-dr", "active":"" },
     { "id":4, "title":"Register!", "url":"/register", "active":"" },
     { "id":5, "title":"Get Started!", "url":"/get-started", "active":"" }
    ]

   $scope.current_page = null;

    $scope.setRoute = function (id) {
       if(id != $scope.current_page.id) {
          $scope.current_page.active = "";
          if(id != -1){
            $location.path($scope.navlinks[id].url);
            $scope.navlinks[id].active = "active";
             $scope.current_page = $scope.navlinks[id];
        } else {
             $scope.current_page = { "id":-1 };
        }
      }
    };

   var path = $location.path();
   if(path == "") path = "/";
   for(var i = 0; i != $scope.navlinks.length; i++){
      if($scope.navlinks[i].url == path){
         $scope.current_page = $scope.navlinks[i];
         $scope.current_page.active = "active";
         break;
      }
   }

   if($scope.current_page == null){
      $scope.current_page = {
         "id":-1,
         "active":""
      };
   }
}
