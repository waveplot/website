
function DownloadsCtrl($scope){
    $scope.selected = {};
    
    $scope.download_active = function() {
        var platform = $scope.selected.linux || $scope.selected.windows;
        var download = $scope.selected.scanner || $scope.selected.binaries || $scope.selected.source;
        return !(platform && download);
    }
}
