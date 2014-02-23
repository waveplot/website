// List of pages with unique identifying string ids.
var pages = {
    'help': ['/help', '/help', {templateUrl: '/app/help/help.html', controller: HelpCtrl, resolve: HelpCtrl.resolve}],
    'latest-downloads': ['/latest-downloads', '/latest-downloads', {templateUrl: '/app/downloads/latest.html', controller: LatestDownloadsController, resolve: LatestDownloadsController.resolve}],
    'all-downloads': ['/all-downloads', '/all-downloads', {templateUrl: '/app/downloads/all.html', controller: AllDownloadsController, resolve: AllDownloadsController.resolve}]
};

function LayoutController($scope, $translatePartialLoader) {
    $translatePartialLoader.addPart('layout');
    
    $scope.blob = "hey!";
}
