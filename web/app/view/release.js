
function ReleaseViewController($scope, $modal, $http, $routeParams){
    $scope.release = {
        "mbid":$routeParams.mbid
    };

    $http.get('/api/release/'+$scope.release.mbid).success(function(data){
        data.tracks.sort(function(a, b) {
            var disc_diff = a.disc_number - b.disc_number;
            if(disc_diff != 0){
                return disc_diff;
            } else {
                return a.track_number - b.track_number;
            }
        });

        $scope.release = data;

        $.each($scope.release.tracks, function(k, v) {
            $http.get('/api/track/'+v.mbid).success(function(data){
                $scope.release.tracks[k] = data;
            });
        });
    });
}
