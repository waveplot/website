'use strict';

function HomeController($scope, $http) {
    $scope.tweets_loaded = false;
    $scope.activity_loaded = false;

    $http.get('/api/tweets').success(function (data) {
        $scope.tweets = data.tweets;
        $scope.tweets_loaded = true;
    });
}

HomeController.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('home');
        return $translate.refresh();
    }
};
