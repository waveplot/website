
function WavePlotViewController($scope, $modal, $http, $routeParams){
    $scope.waveplot = {
        "uuid":$routeParams.uuid
    };

    $scope.links = {
        "expanded":false,
        "icon_class":"fa fa-caret-left"
    };


    $http.get('/api/waveplot/'+$routeParams.uuid).success(function (data) {
        $scope.waveplot = data;
    });

    $http.get('/api/waveplot/'+$routeParams.uuid+"/tracks").success(function (data) {
        $scope.tracks = data.objects;
    });


    $scope.toggleLinks = function() {

        if($scope.links.expanded) {
            $scope.links.icon_class = "fa fa-caret-left";
        } else {
            $scope.links.icon_class = "fa fa-caret-down";
        }

        $scope.links.expanded = !$scope.links.expanded;
    };

    $scope.fullWaveplot = function() {
        $modal.open({
            templateUrl: '/app/view/waveplot-modal.html',
            controller: ModalInstanceCtrl,
            resolve: {
                data: function () {
                    return $scope.waveplot.full;
                }
            }
        });
    };
}

function ModalInstanceCtrl($scope, $modalInstance, $http, data) {
    $scope.data = data;

    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
}
