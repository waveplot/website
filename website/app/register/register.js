
function json_post($http, url, data){
    return $http({
        method: 'POST',
        url: url,
        data:  JSON.stringify(data),
        headers: {'Content-Type': 'application/json'}
    });
}

function RegisterController($scope, $http, $routeParams, $location){
    delete $http.defaults.headers.common['X-Requested-With'];

    $scope.submit = function() {
        json_post($http, '/internal/register', {
            "name":$scope.input.username,
            "email":$scope.input.email
        }).success(function (data) {
            if(data.success === true){
                $scope.mode = 1;
            } else {
                $scope.error = data.message;
            }
        });
    };

    $scope.activate = function() {
        json_post($http, '/internal/activate', {
            "key":$scope.input.key
        }).success(function (data) {
            if(data.success === true){
                $location.path('/');
            } else {
                $scope.error = data.message;
            }
        });
    };

    if($routeParams.key){
        $scope.mode = 1;
        $scope.input = {
            "key": $routeParams.key
        };
    } else {
        $scope.mode = 0;
        $scope.input = {};
    }
}


RegisterController.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('register');
        return $translate.refresh();
    }
};

