'use strict';

function HomeController($scope, $http) {
    $scope.tweets_loaded = false;
    $scope.activity_loaded = false;

    $http.get('/api/tweets').success(function (data) {
        $scope.tweets = data.tweets;
        $scope.tweets_loaded = true;
    });

    $http.get('/api/edit?q={"order_by":[{"field":"edit_time","direction":"desc"}],"limit":"4"}').success(function(data) {
        $scope.activities = data.objects;
        $scope.activity_loaded = true;

        $scope.editors = {};
        $scope.waveplots = {};
        $.each(data.objects, function(k,v) {
            $http.get('/api/editor/'+v.editor.id).success(function(data) {
                $scope.editors[v.editor.id] = data;
            });
        });
    });
}

HomeController.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('home');
        return $translate.refresh();
    }
};
