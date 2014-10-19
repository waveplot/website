// Create main module
var waveplot = angular.module("waveplot", ['waveplot.directives', 'waveplot.filters', 'ngRoute', 'ngSanitize', 'ui.bootstrap', 'pascalprecht.translate']);

// List of pages with unique identifying string ids.
var pages = {
    'help': ['/help', '/help', {templateUrl: '/app/help/help.html', controller: HelpCtrl, resolve: HelpCtrl.resolve}],
    'downloads-windows': ['/downloads/windows', '/downloads/windows', {templateUrl: '/app/downloads/windows.html', controller: DownloadsController, resolve: DownloadsController.resolve}],
    'downloads-linux': ['/downloads/linux', '/downloads/linux', {templateUrl: '/app/downloads/linux.html', controller: DownloadsController, resolve: DownloadsController.resolve}],
    'downloads-other': ['/downloads/other', '/downloads/other', {templateUrl: '/app/downloads/other.html', controller: DownloadsController, resolve: DownloadsController.resolve}],
    'waveplot-view': ['/waveplot/:uuid', '/waveplot/:uuid', {templateUrl: '/app/view/waveplot.html', controller: WavePlotViewController, resolve: WavePlotViewController.resolve}],
    'release-browse': ['/release', '/release', {templateUrl: '/app/browse/browse_release.html', controller: BrowseController, resolve: BrowseController.resolve}],
    'release-view': ['/release/:gid', '/release/:gid', {templateUrl: '/app/view/release.html', controller: ReleaseViewController, resolve: ReleaseViewController.resolve}],
    'artist-browse': ['/artist', '/artist', {templateUrl: '/app/browse/browse_artist.html', controller: BrowseController, resolve: BrowseController.resolve}],
    'register': ['/register', '/register', {templateUrl: '/app/register/register.html', controller: RegisterController, resolve: RegisterController.resolve}],
    'activate': ['/activate/:key', '/activate/:key', {templateUrl: '/app/register/register.html', controller: RegisterController, resolve: RegisterController.resolve}]
};

// Configure the main module
waveplot.config(function ($routeProvider, $locationProvider, $translateProvider, $translatePartialLoaderProvider) {
    // Set up pages in application
    $.each(pages, function (key, value) {
        var match = value[1];
        var info = value[2];
        $routeProvider.when(match, info);
    });

    $routeProvider.otherwise({redirectTo: '/', templateUrl: '/app/home/home.html', controller: HomeController, resolve: HomeController.resolve});

    // Location settings
    $locationProvider.html5Mode(true).hashPrefix('!');

    // Specify the default translations for the menu bar
    $translateProvider.translations('en', {
        "help":"Help",
        "browse": {
            "top":"Browse",
            "artists":"Artists",
            "albums":"Albums",
            "songs":"Songs",
            "dynamic-range":"Dynamic Range"
        },
        "downloads": {
            "top":"Downloads",
            "windows":"Windows",
            "linux":"Linux",
            "other":"Other"
        }
    }).fallbackLanguage('en');

    // Set up other translations
    $translateProvider.useLoader('$translatePartialLoader', {
        urlTemplate: '/app/{part}/i18n/{lang}.json'
    });

    $translateProvider.preferredLanguage('en');
});
