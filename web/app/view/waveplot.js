
function WavePlotViewController($scope, $modal, $http, $routeParams){
    $http.get(server+'/api/waveplot/'+$routeParams.uuid).success(function (data) {
        $scope.waveplot = data;
    });
}
