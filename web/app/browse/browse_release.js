

function BrowseReleaseController($scope, $http){
    $scope.selected = [];
    $scope.releases = [];
    var page_index = 3;

    // Preload two pages of releases to enable infinite scroll.
    $http.get('/api/release?page=1').success(function(data){
        $scope.releases = $scope.releases.concat(data.objects);
        $http.get('/api/release?page=2').success(function(data){
            $scope.releases = $scope.releases.concat(data.objects);
        });
    });

    $scope.get_releases = function(){
        $scope.disable_scroll = "true";
        $http.get('/api/release?page='+page_index).success(function(data){
            $scope.releases = $scope.releases.concat(data.objects);
            $scope.disable_scroll = "false";
        });
        page_index += 1;
    };
}
