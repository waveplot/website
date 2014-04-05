
function json_post($http, url, data){
    return $http({
        method: 'POST',
        url: url,
        data:  $.param(data),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'}
    });
}

function RegisterController($scope, $http){
    delete $http.defaults.headers.common['X-Requested-With'];

    $scope.mode = 0;
    $scope.input = {};

    $scope.submit = function() {
        json_post($http, '/json/editor', {
            "username":$scope.input.username,
            "email":$scope.input.email
        }).success(function (data) {
            if(data.result == "success"){
                $scope.mode = 1;
            } else {
                $scope.error = data.error;
            }
        });
    };

    $scope.activate = function() {
        json_post($http, '/json/activate', {
            "key":$scope.input.pin
        }).success(function (data) {
            if(data.result == "success"){
                $scope.mode = 2;
            } else {
                $scope.error = data.error;
            }
        });
    };
}


RegisterController.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('register');
        return $translate.refresh();
    }
};

