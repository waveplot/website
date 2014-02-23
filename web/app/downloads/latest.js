
function LatestDownloadsController($scope){
    $scope.windows = false;
    $scope.linux = false;
    $scope.scanner = false;
    $scope.binaries = false;
    $scope.source = false;
    
    $scope.download_active = function() {
        var platform = (!$scope.windows && !$scope.linux) || ($scope.windows && $scope.linux);
        var item = (!$scope.scanner && !$scope.binaries && !$scope.source);
        return platform || item;
    };
    
    $scope.download = function() {
        // TODO - Need to set the file correctly based on user selection
        window.location = '/assets/downloads/libwaveplot.tar.gz';
    }
}


LatestDownloadsController.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('downloads');
        return $translate.refresh();
    }
}
