
function WavePlotViewController($scope, $modal, $http, $routeParams){
    $scope.waveplot = {
        "uuid":$routeParams.uuid
    }

    $scope.links = {
        "expanded":false,
        "icon_class":"fa fa-caret-left"
    }


    $http.get(server+'/api/waveplot/'+$routeParams.uuid).success(function (data) {
        $scope.waveplot = data;
    });

    $http.get(server+'/api/waveplot/'+$routeParams.uuid+'/preview').success(function (data) {
        $scope.waveplot.preview = data.data;
    });

    $scope.toggleLinks = function() {

        if($scope.links.expanded) {
            $scope.links.icon_class = "fa fa-caret-left";
        } else {
            $scope.links.icon_class = "fa fa-caret-down";
        }

        $scope.links.expanded = !$scope.links.expanded;
    }

    $scope.fullWaveplot = function() {
        var modalInstance = $modal.open({
            templateUrl: '/app/view/waveplot-modal.html',
            controller: ModalInstanceCtrl,
            resolve: {
                uuid: function () {
                    return $scope.waveplot.uuid;
                }
            }
        });
    }
}

function ModalInstanceCtrl($scope, $modalInstance, $http, uuid) {
    $http.get(server+'/api/waveplot/'+uuid+'/full').success(function (data) {
        $scope.data = data.data;
    });

    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
};
