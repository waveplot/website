

function BrowseController($scope, $http, $timeout){
    $scope.selected = [];
    $scope.collection = [];
    $scope.page = 1;
    $scope.type = "";

    $scope.items_per_page_options = [
        {name:"6 items per page", value:6},
        {name:"12 items per page", value:12},
        {name:"24 items per page", value:24},
        {name:"48 items per page", value:48}
    ];

    $scope.items_per_page = 12;


    $scope.incrementPage = function(){
        $scope.page++;
    };

    $scope.decrementPage = function(){
        if($scope.page === 1) return;

        $scope.page--;
    };

    $scope.update_collection = function(){
        $http.get('/api/'+$scope.type+'?offset='+(($scope.page-1)*$scope.items_per_page).toString()+'&limit='+$scope.items_per_page).success(function(data){
            $scope.collection = data.objects;
        });
    };

    $scope.$watch('page', function(newValue, oldValue) {
        if(newValue < 1){
            $scope.page = 1;
            return;
        }

        $scope.update_collection();
    });

    $scope.$watch('items_per_page', function(newValue, oldValue) {
        $scope.update_collection();
    });
}
