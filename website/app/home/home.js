'use strict';

function HomeController($scope, $http) {
    $scope.tweets_loaded = false;
    $scope.activity_loaded = false;

    $http.get('/internal/tweets').success(function (data) {
        $scope.tweets = data.tweets;
        $scope.tweets_loaded = true;
    });

    $http.get('/internal/changes').success(function(data) {
        $scope.activities = data.objects;
        $scope.activity_loaded = true;
    });

    $scope.get_download_link = function(){
        var split = navigator.platform.indexOf(' ', 6);
        var platform = navigator.platform.toLowerCase();

        if(split > -1) {
            platform = platform.substr(0, split);
        }

        if(platform == 'linux i686' || platform == 'linux x86_64') {
            return '/downloads/linux';
        } else if (platform == 'win32') {
            return '/downloads/windows';
        } else {
            return '/downloads/other';
        }
    }
}

HomeController.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('home');
        return $translate.refresh();
    }
};
