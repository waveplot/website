angular.module('waveplot', ['ui.bootstrap', 'pascalprecht.translate']).
    config(['$routeProvider','$locationProvider','$translateProvider', function($routeProvider,$locationProvider,$translateProvider) {
            $routeProvider.
                when('/waveplot/:uuid', {templateUrl: '/partials/waveplot_uuid.html', controller: WavePlotUUIDCtrl}).
                when('/recording/:mbid', {templateUrl: '/partials/recording_mbid.html', controller: RecordingMBIDCtrl});

            $routeProvider.
                when('/list/waveplot', {templateUrl: '/partials/waveplot_list.html', controller: WavePlotListCtrl}).
                when('/list/recording', {templateUrl: '/partials/recording_list.html', controller: RecordingListCtrl});

            $routeProvider.
                when('/get-started', {templateUrl: '/partials/get_started.html'}).
                when('/extreme-dr', {templateUrl: '/partials/extreme_dr.html', controller: ExtremeDRCtrl}).
                when('/register', {templateUrl: '/partials/register.html', controller: RegisterCtrl}).
                when('/activate/:key', {templateUrl: '/partials/activate.html', controller: ActivateCtrl}).
                otherwise({redirectTo: '', templateUrl: '/partials/home.html'});

            $locationProvider.html5Mode(true).hashPrefix('!');

            $translateProvider.translations('en', {
                TITLE: 'Welcome to WavePlot!',
                LEAD: 'WavePlot is a project designed to collect information about audio files, and make it available to everyone. Our data is free, our source code is open, and we want you to get involved!'
            });

            $translateProvider.translations('fr', {
                TITLE: 'Bienvenue à WavePlot!',
                LEAD: 'WavePlot est un projet conçu pour collecter des informations sur les fichiers audio, et de le rendre accessible à tous. Nos données sont libres, notre code source est ouvert, et nous voulons que vous vous impliquer!'
            });

            $translateProvider.translations('de', {
                TITLE: 'Willkommen auf WavePlot!',
                LEAD: 'WavePlot ist ein Projekt entwickelt, um Informationen über die Audio-Dateien sammeln, und machen es für jedermann zugänglich. Unsere Daten frei ist, ist unser Quellcode offen, und wir möchten, dass Sie sich zu engagieren!'
            });

            $translateProvider.translations('es', {
                TITLE: 'Bienvenido a WavePlot!',
                LEAD: 'WavePlot es un proyecto diseñado para recoger información sobre los archivos de audio, y ponerla a disposición de todo el mundo. ¡Nuestra información es libre, el código fuente es abierto, y queremos que usted participe!'
            });

            $translateProvider.translations('jp', {
                TITLE: 'WavePlotへようこそ！',
                LEAD: 'WavePlotは、オーディオファイルに関する情報を収集し、誰もが利用できるように設計されたプロジェクトです。我々のデータは無料ですが、我々のソースコードはオープンであり、我々はあなたが関わって取得したい！'
            });

            $translateProvider.translations('cn', {
                TITLE: '欢迎WavePlot！',
                LEAD: 'WavePlot是一个项目，旨在收集有关音频文件的信息，提供给大家。我们的数据是免费的，我们的源代码是开放的，我们希望您积极参与！'
            });

            $translateProvider.preferredLanguage('en');
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

function MainCtrl($scope, $location, $translate) {
    $scope.navlinks = [
      { "id":0, "title":"Home", "url":"/", "active":"" },
      { "id":1, "title":"List WavePlots", "url":"/list/waveplot", "active":"" },
     { "id":2, "title":"Recordings with Multiple Waveplots", "url":"/list/recording", "active":"" },
     { "id":3, "title":"Extreme D.R.", "url":"/extreme-dr", "active":"" },
     { "id":4, "title":"Register!", "url":"/register", "active":"" },
     { "id":5, "title":"Get Started!", "url":"/get-started", "active":"" }
    ]

$scope.changeLanguage = function (key) {
    $translate.uses(key);
  };

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
