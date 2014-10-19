
function ReleaseViewController($scope, $modal, $http, $routeParams){
    $scope.release = {
        "gid":$routeParams.gid
    };

    $http.get('/api/release/'+$scope.release.gid).success(function(data){
        $scope.release = data;
        $http.get($scope.release.artist_credit).success(function(data){
            $scope.artist_credit = data;
        });
    });

    $http.get('/api/release/'+$scope.release.gid+'/media').success(function(data){
        $scope.media = data.objects;
        $.each($scope.media, function(k, v) {
            $http.get(v.url+'/tracks').success(function(data){
                v.tracks = data.objects;
            });
        });
    });

    $scope.loadWavePlots = function(track){
        if(!("waveplots" in track)){
            $http.get(track.url+'/waveplots').success(function(data){
                track.waveplots = data.objects;

                if(track.waveplots.length == 0){
                    track.has_waveplots = false;
                }
            });
        }
    }

    $scope.loadAllWavePlots = function(medium){
        $.each(medium.tracks, function(k,t){
            $scope.loadWavePlots(t);
        });
    }
}
