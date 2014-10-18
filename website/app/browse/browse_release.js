

function BrowseReleaseController($scope, $http, $timeout){
    $scope.selected = [];
    $scope.releases = [];
    $scope.filter = "";
    var waiting_pages = {};
    var load_next = 1;
    var display_next = 1;
    $scope.check = true;

    $scope.get_releases = function(){
        var filters = [
        ];

            filters.push({"name":"title", "op":"like", "val":"%"+$scope.filter});
            filters.push({"name":"title", "op":"like", "val":$scope.filter+"%"});
            filters.push({"name":"title", "op":"like", "val":"%"+$scope.filter+"%"});

        var query_string = 'q={"filters":'+JSON.stringify(filters)+',"order_by":[{"field":"title","direction":"asc"}],"disjunction":true}';
        $http.get('/api/release?page='+load_next+'&'+query_string).success(function(data){
            waiting_pages[data.page] = data.objects;

            // Check whether next page is ready for display
            while(display_next in waiting_pages){
                $scope.releases = $scope.releases.concat(waiting_pages[display_next]);
                display_next += 1;
            }
        });
        load_next += 1;
    };

    $scope.filter_releases = function(){
        var filterTextTimeout;

        $scope.$watch('filter', function () {
            if (filterTextTimeout) $timeout.cancel(filterTextTimeout);

            filterTextTimeout = $timeout(function() {
                $scope.releases = [];
                waiting_pages = {};
                load_next = 1;
                display_next = 1;
                $scope.get_releases();
            }, 250);
        });
    }

    $scope.get_releases();
}
