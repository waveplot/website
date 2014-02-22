// List of pages with unique identifying string ids.
var pages = {
    'help': ['/help', '/help', {templateUrl: '/app/help/help.html', controller: HelpCtrl, resolve: HelpCtrl.resolve}],
    'downloads': ['/downloads', '/downloads', {templateUrl: '/app/downloads/downloads.html', controller: DownloadsCtrl, resolve: DownloadsCtrl.resolve}]
};

function LayoutController($scope, $translatePartialLoader) {
    $translatePartialLoader.addPart('layout');
    
    $scope.blob = "hey!";
}
