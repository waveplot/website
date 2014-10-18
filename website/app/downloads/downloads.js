
function DownloadsController($scope, $modal, $http){

}

DownloadsController.resolve = {
    lang: function($translate, $translatePartialLoader, $q){
        $translatePartialLoader.addPart('downloads');
        return $translate.refresh();
    }
};
