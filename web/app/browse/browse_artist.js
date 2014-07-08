

function BrowseArtistController($scope, $http, $timeout){
    $scope.selected = [];
    $scope.artists = [];
    $scope.filter = "";
    var waiting_pages = {};
    var load_next = 1;
    var display_next = 1;
    $scope.check = true;

    $scope.get_artists = function(){
        var filters = [
        ];

            filters.push({"name":"name", "op":"like", "val":"%"+$scope.filter});
            filters.push({"name":"name", "op":"like", "val":$scope.filter+"%"});
            filters.push({"name":"name", "op":"like", "val":"%"+$scope.filter+"%"});

        var query_string = 'q={"filters":'+JSON.stringify(filters)+',"order_by":[{"field":"name","direction":"asc"}],"disjunction":true}';
        $http.get('/api/artist?page='+load_next+'&'+query_string).success(function(data){
            waiting_pages[data.page] = data.objects;

            // Check whether next page is ready for display
            while(display_next in waiting_pages){
                $scope.artists = $scope.artists.concat(waiting_pages[display_next]);
                display_next += 1;
            }
        });
        load_next += 1;
    };

    $scope.filter_artists = function(){
        var filterTextTimeout;

        $scope.$watch('filter', function () {
            if (filterTextTimeout) $timeout.cancel(filterTextTimeout);

            filterTextTimeout = $timeout(function() {
                $scope.artists = [];
                waiting_pages = {};
                load_next = 1;
                display_next = 1;
                $scope.get_artists();
                $scope.get_artists();
            }, 250);
        });
    }

    $scope.get_artists();
    $scope.get_artists();
}
